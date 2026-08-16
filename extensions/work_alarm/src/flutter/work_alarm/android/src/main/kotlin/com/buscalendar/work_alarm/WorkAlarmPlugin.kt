package com.buscalendar.work_alarm

import android.Manifest
import android.app.Activity
import android.app.AlarmManager
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.util.Log
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.embedding.engine.plugins.activity.ActivityAware
import io.flutter.embedding.engine.plugins.activity.ActivityPluginBinding
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.PluginRegistry
import org.json.JSONArray
import org.json.JSONObject

class WorkAlarmPlugin : FlutterPlugin, MethodChannel.MethodCallHandler, ActivityAware,
    PluginRegistry.RequestPermissionsResultListener, PluginRegistry.ActivityResultListener {
    private lateinit var context: Context
    private lateinit var channel: MethodChannel
    private var activity: Activity? = null
    private var activityBinding: ActivityPluginBinding? = null
    private var notificationPermissionResult: MethodChannel.Result? = null
    private var exactAlarmSettingsResult: MethodChannel.Result? = null
    private var fullScreenSettingsResult: MethodChannel.Result? = null

    override fun onAttachedToEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        context = binding.applicationContext
        channel = MethodChannel(binding.binaryMessenger, CHANNEL_NAME)
        channel.setMethodCallHandler(this)
    }

    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel.setMethodCallHandler(null)
    }

    override fun onAttachedToActivity(binding: ActivityPluginBinding) = attachActivity(binding)

    override fun onReattachedToActivityForConfigChanges(binding: ActivityPluginBinding) =
        attachActivity(binding)

    override fun onDetachedFromActivityForConfigChanges() = detachActivity()

    override fun onDetachedFromActivity() = detachActivity()

    private fun attachActivity(binding: ActivityPluginBinding) {
        activity = binding.activity
        activityBinding = binding
        binding.addRequestPermissionsResultListener(this)
        binding.addActivityResultListener(this)
    }

    private fun detachActivity() {
        activityBinding?.removeRequestPermissionsResultListener(this)
        activityBinding?.removeActivityResultListener(this)
        activityBinding = null
        activity = null
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        try {
            when (call.method) {
                "getPermissionStatus" -> result.success(permissionStatus())
                "requestNotificationPermission" -> requestNotificationPermission(result)
                "openExactAlarmSettings" -> openExactAlarmSettings(result)
                "openFullScreenSettings" -> openFullScreenSettings(result)
                "getNativeSnapshot" -> result.success(jsonToValue(AlarmStore(context).readSnapshot()))
                "reconcile" -> result.success(reconcile(call.arguments))
                "cancelAll" -> result.success(cancelAll())
                "stopRinging" -> result.success(stopRinging())
                "testAlarm" -> result.success(testAlarm())
                else -> result.notImplemented()
            }
        } catch (error: Exception) {
            AlarmStore(context).recordFailure(
                "native_method_failed:${call.method}:${error.javaClass.simpleName}:${error.message.orEmpty()}",
            )
            result.error("work_alarm_native_error", error.message, null)
        }
    }

    private fun notificationsGranted(): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED

    private fun permissionStatus(): Map<String, Any> {
        val notificationGranted = notificationsGranted()
        val exactGranted = AlarmScheduler(context).canScheduleExactAlarms()
        val fullScreenGranted = canUseFullScreenIntent()
        if (notificationGranted) Log.i(PERMISSION_TAG, "Notification granted")
        if (exactGranted) Log.i(PERMISSION_TAG, "Exact alarm granted")
        if (fullScreenGranted) Log.i(PERMISSION_TAG, "Full screen alarm granted")
        return mapOf(
            "supported" to true,
            "notifications_granted" to notificationGranted,
            "exact_alarm_granted" to exactGranted,
            "full_screen_granted" to fullScreenGranted,
            "can_start_alarm" to (notificationGranted && exactGranted),
            "sdk_int" to Build.VERSION.SDK_INT,
            "stage" to 5,
        )
    }

    private fun canUseFullScreenIntent(): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE ||
            context.getSystemService(NotificationManager::class.java).canUseFullScreenIntent()

    private fun requestNotificationPermission(result: MethodChannel.Result) {
        if (notificationsGranted() || Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            Log.i(PERMISSION_TAG, "Notification granted")
            result.success(permissionStatus())
            return
        }
        val currentActivity = activity
            ?: throw IllegalStateException("Notification permission requires an attached Activity")
        check(notificationPermissionResult == null) { "Notification permission request already active" }
        notificationPermissionResult = result
        Log.i(PERMISSION_TAG, "Notification permission requested")
        ActivityCompat.requestPermissions(
            currentActivity,
            arrayOf(Manifest.permission.POST_NOTIFICATIONS),
            REQUEST_NOTIFICATION_PERMISSION,
        )
    }

    private fun openExactAlarmSettings(result: MethodChannel.Result) {
        if (AlarmScheduler(context).canScheduleExactAlarms() || Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            Log.i(PERMISSION_TAG, "Exact alarm granted")
            result.success(permissionStatus())
            return
        }
        val currentActivity = activity
            ?: throw IllegalStateException("Exact alarm settings require an attached Activity")
        check(exactAlarmSettingsResult == null) { "Exact alarm settings request already active" }
        exactAlarmSettingsResult = result
        Log.i(PERMISSION_TAG, "Exact alarm settings opened")
        val intent = Intent(
            Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,
            Uri.parse("package:${context.packageName}"),
        )
        currentActivity.startActivityForResult(intent, REQUEST_EXACT_ALARM_SETTINGS)
    }

    private fun openFullScreenSettings(result: MethodChannel.Result) {
        if (canUseFullScreenIntent() || Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            Log.i(PERMISSION_TAG, "Full screen alarm granted")
            result.success(permissionStatus())
            return
        }
        val currentActivity = activity
            ?: throw IllegalStateException("Full screen alarm settings require an attached Activity")
        check(fullScreenSettingsResult == null) { "Full screen alarm settings request already active" }
        fullScreenSettingsResult = result
        Log.i(PERMISSION_TAG, "Full screen alarm settings opened")
        val intent = Intent(
            Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
            Uri.parse("package:${context.packageName}"),
        )
        currentActivity.startActivityForResult(intent, REQUEST_FULL_SCREEN_SETTINGS)
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ): Boolean {
        if (requestCode != REQUEST_NOTIFICATION_PERMISSION) return false
        val pending = notificationPermissionResult ?: return true
        notificationPermissionResult = null
        val status = permissionStatus()
        Log.i(PERMISSION_TAG, "Notification result granted=${status["notifications_granted"]}")
        pending.success(status)
        return true
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?): Boolean {
        val status = permissionStatus()
        if (requestCode == REQUEST_EXACT_ALARM_SETTINGS) {
            val pending = exactAlarmSettingsResult ?: return true
            exactAlarmSettingsResult = null
            Log.i(PERMISSION_TAG, "Exact alarm result granted=${status["exact_alarm_granted"]}")
            pending.success(status)
            return true
        }
        if (requestCode == REQUEST_FULL_SCREEN_SETTINGS) {
            val pending = fullScreenSettingsResult ?: return true
            fullScreenSettingsResult = null
            Log.i(PERMISSION_TAG, "Full screen result granted=${status["full_screen_granted"]}")
            pending.success(status)
            return true
        }
        return false
    }

    private fun reconcile(arguments: Any?): Map<String, Any> {
        Log.i(RECONCILE_TAG, "started")
        val outer = arguments as? Map<*, *>
            ?: throw IllegalArgumentException("reconcile arguments must be an object")
        val snapshotMap = outer["snapshot"] as? Map<*, *>
            ?: throw IllegalArgumentException("reconcile requires snapshot")
        val desiredSnapshot = valueToJson(snapshotMap) as JSONObject
        val desired = parseAlarms(desiredSnapshot)

        val store = AlarmStore(context)
        val scheduler = AlarmScheduler(context)
        val existing = store.readAlarms().associateBy { it.alarmId }
        val desiredById = desired.associateBy { it.alarmId }

        var scheduled = 0
        var updated = 0
        var cancelled = 0
        var unchanged = 0
        val failures = mutableListOf<String>()
        val persisted = mutableListOf<StoredAlarm>()

        for ((alarmId, oldAlarm) in existing) {
            val replacement = desiredById[alarmId]
            if (replacement == null || !sameReservation(oldAlarm, replacement)) {
                scheduler.cancel(oldAlarm)
                cancelled += 1
            }
        }

        for (alarm in desired) {
            val oldAlarm = existing[alarm.alarmId]
            if (oldAlarm != null && sameReservation(oldAlarm, alarm)) {
                unchanged += 1
                persisted.add(alarm)
                continue
            }
            if (scheduler.schedule(alarm)) {
                if (oldAlarm == null) scheduled += 1 else updated += 1
                persisted.add(alarm)
            } else {
                failures.add("${alarm.alarmId}:exact_alarm_permission_missing")
            }
        }

        val syncedAt = System.currentTimeMillis()
        desiredSnapshot.put(
            "alarms",
            JSONArray().apply { persisted.forEach { put(it.payload) } },
        )
        store.writeSnapshot(desiredSnapshot)
        store.recordSync(syncedAt)
        if (failures.isEmpty()) store.clearFailure() else store.recordFailure(failures.joinToString(";"))
        Log.i(RECONCILE_TAG, "scheduled=$scheduled updated=$updated cancelled=$cancelled")

        return mapOf(
            "scheduled" to scheduled,
            "updated" to updated,
            "cancelled" to cancelled,
            "unchanged" to unchanged,
            "failed" to failures.size,
            "failures" to failures,
            "reserved_count" to persisted.size,
            "last_sync_at" to syncedAt,
            "stage" to 5,
            "native_scheduling" to true,
        )
    }

    private fun cancelAll(): Map<String, Any> {
        val store = AlarmStore(context)
        val scheduler = AlarmScheduler(context)
        val alarms = store.readAlarms()
        alarms.forEach(scheduler::cancel)
        store.writeSnapshot(AlarmStore.emptySnapshot())
        store.recordSync(System.currentTimeMillis())
        store.clearFailure()
        return mapOf("cancelled" to alarms.size, "stage" to 5)
    }

    private fun stopRinging(): Map<String, Any> {
        val stopped = context.stopService(Intent(context, AlarmRingingService::class.java))
        AlarmStore(context).setCurrentAlarm(null)
        Log.i("AlarmStop", "stop requested stopped=$stopped")
        return mapOf("stopped" to stopped, "stage" to 5)
    }

    private fun testAlarm(): Map<String, Any> {
        val alarmId = "test:${System.currentTimeMillis()}"
        val requestCode = (System.currentTimeMillis() % 1_000_000_000L).toInt().coerceAtLeast(1)
        val payload = JSONObject().apply {
            put("title", "버스캘린더 테스트 알람")
            put("message", "알람 소리와 진동을 확인하세요.")
            put("sound_enabled", true)
            put("vibration_enabled", true)
        }
        Log.i(TEST_ALARM_TAG, "started alarm_id=$alarmId")
        val intent = Intent(AlarmScheduler.ACTION_ALARM_FIRED).apply {
            setClass(context, AlarmReceiver::class.java)
            setPackage(context.packageName)
            putExtra("alarm_id", alarmId)
            putExtra("request_code", requestCode)
            putExtra("trigger_at", System.currentTimeMillis())
            putExtra("payload", payload.toString())
        }
        context.sendBroadcast(intent)
        Log.i(TEST_ALARM_TAG, "completed alarm_id=$alarmId")
        return mapOf("started" to true, "alarm_id" to alarmId, "stage" to 5)
    }

    private fun parseAlarms(snapshot: JSONObject): List<StoredAlarm> {
        val alarms = snapshot.optJSONArray("alarms") ?: JSONArray()
        return buildList {
            for (index in 0 until alarms.length()) {
                val item = alarms.optJSONObject(index) ?: continue
                val alarmId = item.optString("alarm_id")
                val requestCode = item.optInt("request_code", -1)
                val triggerAt = item.optLong("trigger_at", -1L)
                require(alarmId.isNotBlank()) { "alarm_id is required" }
                require(requestCode > 0) { "request_code must be positive" }
                require(triggerAt > 0L) { "trigger_at must be positive" }
                add(StoredAlarm(alarmId, requestCode, triggerAt, item))
            }
        }
    }

    private fun sameReservation(left: StoredAlarm, right: StoredAlarm): Boolean =
        left.requestCode == right.requestCode && left.triggerAt == right.triggerAt &&
            RESERVATION_FIELDS.all { field ->
                (left.payload.opt(field) ?: JSONObject.NULL).toString() ==
                    (right.payload.opt(field) ?: JSONObject.NULL).toString()
            }

    private fun valueToJson(value: Any?): Any = when (value) {
        null -> JSONObject.NULL
        is Map<*, *> -> JSONObject().apply {
            value.forEach { (key, child) -> put(key.toString(), valueToJson(child)) }
        }
        is Iterable<*> -> JSONArray().apply { value.forEach { put(valueToJson(it)) } }
        else -> value
    }

    private fun jsonToValue(value: Any?): Any? = when (value) {
        JSONObject.NULL -> null
        is JSONObject -> value.keys().asSequence().associateWith { jsonToValue(value.get(it)) }
        is JSONArray -> (0 until value.length()).map { jsonToValue(value.get(it)) }
        else -> value
    }

    companion object {
        private const val CHANNEL_NAME = "work_alarm/native"
        private const val REQUEST_NOTIFICATION_PERMISSION = 7302
        private const val REQUEST_EXACT_ALARM_SETTINGS = 7303
        private const val REQUEST_FULL_SCREEN_SETTINGS = 7304
        private const val PERMISSION_TAG = "Permission"
        private const val RECONCILE_TAG = "Reconcile"
        private const val TEST_ALARM_TAG = "TestAlarm"
        private val RESERVATION_FIELDS = listOf(
            "alarm_id", "date", "shift", "status", "title", "message",
            "sound_enabled", "vibration_enabled",
            "first_trip", "memo",
        )
    }
}
