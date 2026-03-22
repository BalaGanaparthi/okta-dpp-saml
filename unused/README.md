# Unused / Legacy Code

This folder contains code that is **not being used** in the current application but is kept for reference.

## Files

### `device_checker.py`
**Original Purpose:** Device posture validation and checking logic

**Why Moved Here:**
- The application now operates in **simulation mode only**
- Users manually select `isManaged` and `isCompliant` via UI
- No actual device checking or validation is performed
- The `DeviceChecker` class and its validation logic are not used

**What's Still Used:**
- The `DevicePosture` class (data structure only) has been moved to `src/models.py`
- This provides a simple data container for device posture information

## Simulation Mode

The current application:
1. ✅ Accepts user input for `isManaged` and `isCompliant`
2. ✅ Creates a `DevicePosture` object with user-provided values
3. ✅ Includes this in the SAML response
4. ❌ Does NOT perform any actual device validation
5. ❌ Does NOT check MDM status
6. ❌ Does NOT verify OS versions
7. ❌ Does NOT validate encryption status

This is intentional - the app is a **Device Posture Provider simulator** for testing purposes.

## If You Need Actual Device Checking

If you want to implement real device validation:

1. Use the `DeviceChecker` class from this folder
2. Integrate with MDM APIs (Intune, Jamf, etc.)
3. Implement OS version checking
4. Add encryption verification
5. Update `src/app.py` to call validation methods

**Warning:** This will change the application from a simulator to an actual validation system.

---

**Current State:** Simulation mode only (no actual checking)
**Future State:** Could be extended to perform real device validation if needed
