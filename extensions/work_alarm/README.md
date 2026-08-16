# Work Alarm Flet extension

Local Flet service extension for the Bus Calendar Android alarm feature.

The extension now contains the persistent Android alarm implementation through
Stage 5: exact scheduling, boot restoration, ringing/stop receivers, the
foreground ringing service, runtime permission handling, diagnostics, and the
Python-to-Flutter bridge used by the settings screen.

Non-Android and web clients keep the same Python project but return an
unsupported status without invoking Android APIs.
