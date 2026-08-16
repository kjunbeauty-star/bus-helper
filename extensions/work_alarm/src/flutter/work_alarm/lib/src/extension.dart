import 'package:flet/flet.dart';

import 'work_alarm_service.dart';

class Extension extends FletExtension {
  @override
  FletService? createService(Control control) {
    switch (control.type) {
      case "WorkAlarmService":
        return WorkAlarmServiceControl(control: control);
      default:
        return null;
    }
  }
}
