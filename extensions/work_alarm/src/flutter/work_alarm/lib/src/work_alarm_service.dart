import 'package:flet/flet.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

class WorkAlarmServiceControl extends FletService {
  static const MethodChannel _nativeChannel =
      MethodChannel('work_alarm/native');

  Map<String, dynamic> _snapshot = _emptySnapshot();

  WorkAlarmServiceControl({required super.control});

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_invokeMethod);
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    debugPrint("WorkAlarmService.$name($args)");
    switch (name) {
      case "ping":
        return {
          "ok": true,
          "bridge": "flutter",
          "stage": _supportsNativeAndroid ? 4 : 2,
          "native_android": _supportsNativeAndroid,
        };
      case "get_permission_status":
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap("getPermissionStatus");
        }
        return _unsupportedPermissionStatus();
      case "request_notification_permission":
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap("requestNotificationPermission");
        }
        return _unsupportedPermissionStatus();
      case "open_exact_alarm_settings":
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap("openExactAlarmSettings");
        }
        return _unsupportedPermissionStatus();
      case "open_full_screen_settings":
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap("openFullScreenSettings");
        }
        return _unsupportedPermissionStatus();
      case "reconcile":
        final candidate = args is Map ? args["snapshot"] : null;
        if (candidate is! Map) {
          throw ArgumentError("reconcile requires a snapshot object");
        }
        _snapshot = Map<String, dynamic>.from(candidate);
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap(
            "reconcile",
            {"snapshot": _snapshot},
          );
        }
        final alarms = _snapshot["alarms"];
        final count = alarms is List ? alarms.length : 0;
        return {
          "scheduled": 0,
          "updated": 0,
          "cancelled": 0,
          "unchanged": count,
          "stage": 2,
          "native_scheduling": false,
        };
      case "cancel_all":
        _snapshot = _emptySnapshot();
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap("cancelAll");
        }
        return {"cancelled": true, "stage": 2};
      case "stop_ringing":
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap("stopRinging");
        }
        return {"stopped": false, "reason": "ringing_service_not_implemented"};
      case "get_native_snapshot":
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap("getNativeSnapshot");
        }
        return Map<String, dynamic>.from(_snapshot);
      case "test_alarm":
        if (_supportsNativeAndroid) {
          return await _invokeNativeMap("testAlarm");
        }
        return {"started": false, "reason": "android_only"};
      default:
        throw UnsupportedError("Unknown WorkAlarmService method: $name");
    }
  }

  bool get _supportsNativeAndroid =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

  Future<Map<String, dynamic>> _invokeNativeMap(
    String method, [
    Map<String, dynamic>? arguments,
  ]) async {
    final response = await _nativeChannel.invokeMapMethod<String, dynamic>(
      method,
      arguments,
    );
    return Map<String, dynamic>.from(response ?? const {});
  }

  @override
  void dispose() {
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }
}

Map<String, dynamic> _emptySnapshot() => {
      "schema_version": 1,
      "alarms": <dynamic>[],
      "stage": 2,
      "native_persistence": false,
    };

Map<String, dynamic> _unsupportedPermissionStatus() => {
      "supported": false,
      "notifications_granted": false,
      "exact_alarm_granted": false,
      "full_screen_granted": false,
      "can_start_alarm": false,
      "reason": "android_native_not_implemented",
    };
