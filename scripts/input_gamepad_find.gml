/// input_gamepad_find()
// Device slots are platform-defined; do not assume a fixed twelve-slot table.
for (var i = 0; i < gamepad_get_device_count(); i++) {
    if (gamepad_is_connected(i)) {
        return i;
    }
}
// Preserve the existing sentinel. Callers must check connectivity before polling.
return 0;
