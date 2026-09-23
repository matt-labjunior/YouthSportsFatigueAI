# Mimic a wearable with Scratch and connect it to the app

The included `WearableSimulator.sb3` is an ordinary Scratch 3 project. It generates fictional heart rate and elapsed activity minutes every five seconds. Sleep, soreness, and energy are manually set sliders; they are not measured by this simulator. Keys 1, 2, and 3 switch among Player-01, Player-02, and Player-03.

**Automatic network publishing uses TurboWarp, a Scratch-compatible editor, plus the included custom extension.** The standard Scratch project runs the simulation but does not itself make the authenticated HTTP requests. This package supplies the bridge and relay source; it does not supply a hosted endpoint or actual wearable hardware.

## Data flow

Scratch variables → TurboWarp extension → authenticated HTTPS relay → App Inventor's periodic Web requests → local ML model → per-student history and graph.

The simulator updates every 5 seconds; the app's minimum polling interval is 15 seconds. The relay stores only the latest reading for each alias, so intermediate samples can be skipped. App history records samples the app actually retrieves and classifies.

## 1. Run the relay

Python 3 is required. The relay has no third-party dependencies.

```bash
export RELAY_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python3 relay.py
```

Keep the same token for the TurboWarp session and the app's endpoint bearer-token field. Do not put it in a publicly shared project or screenshot. The example creates a token in your shell; retrieve its value privately when configuring the two clients.

By default the relay listens on 127.0.0.1:8080, for a reverse proxy running on the same computer. For iPhone access you must expose it through an HTTPS reverse proxy/tunnel with a trusted certificate, or deploy it on an HTTPS-capable host. Configure that service to forward to this relay. The public address below is a placeholder:

`https://your-relay.example`

For container hosts, set `RELAY_HOST=0.0.0.0` and the provider's `PORT`. Direct TLS is also supported with TLS_CERT and TLS_KEY pointing to a certificate/key trusted by your phone. Do not substitute localhost in the iPhone endpoint; that means the phone itself. Certificate provisioning and deployment are not included or performed by this package.

The server requires a bearer token for both reading and writing. It accepts only simulated data and holds at most 1,000 aliases in memory. Restarting it clears the readings. Its browser CORS origin is https://turbowarp.org. Keep it limited to the demonstration; it is not a production medical-data service.

## 2. Open the Scratch simulator

1. Open https://turbowarp.org/editor on your computer.
2. Use File → Load from your computer to open WearableSimulator.sb3.
3. Add a **Custom Extension**, load `turbowarp-wearable.js` from file, and select **Run without sandbox**. This grants the extension access to the project's stage variables. Only use this supplied, reviewable source.
4. Click the green flag. HeartRate and ActivityMin update; ReadingSeq increases every five seconds.
5. Adjust Intensity, SleepHours, Soreness, and Energy using the visible sliders.
6. In the Simulated Wearable extension category, set the **start streaming to** block to your HTTPS relay base address and click it. Paste the relay token into the prompt. The token is kept only in the current extension session.
7. Allow the requested network access. The **stream status** reporter should say `Sent SIMULATED Player-01 #...`.
8. Press 2 or 3 to switch aliases and wait for the next generated reading. Use the extension's **stop streaming** block or the project's red Stop button to stop. One request already in flight may still reach the relay.

Start the green flag before streaming. The project stop event stops the extension. To resume after stopping/restarting, click the start streaming block again and supply the token.

The extension sends only when ReadingSeq changes, preventing a stopped simulation from refreshing stale data. Recognized session credentials are never written to Scratch variables or the SB3 file.

## 3. Connect the app

In **Team**:

- Add matching aliases: Player-01, Player-02, Player-03.
- For each alias, check **Include selected athlete in polling**.
- Mode: **Remote readings**.
- Interval: **15** seconds.
- Maximum reading age: **15** minutes.
- Endpoint: `https://your-relay.example/readings/{athleteId}`.
- Endpoint bearer token: the same RELAY_TOKEN.
- Tap **Poll now** or **Start**.

Generate at least one reading for each included alias first; otherwise that alias correctly returns HTTP 404. Leave the app open. Check History for SIMULATED wearable entries and switch aliases to see their graphs. Polling repeatedly before a new reading appears does not duplicate a history row.

Example relay response:

```json
{
  "athleteId": "Player-01",
  "timestamp": "2026-09-23T15:00:00.000Z",
  "simulated": true,
  "heart_rate": 135,
  "sleep_hours": 8,
  "activity_minutes": 20,
  "soreness": 2,
  "energy": 4
}
```

The timestamp is assigned when a new simulated sample reaches the relay. It is a demo receipt timestamp, not a physical sensor's capture timestamp.

## What a real wearable would change

A real device needs a supported sensor SDK, Bluetooth integration, or vendor API to provide actual measurements. Scratch does not create biometric sensors. A replacement adapter can expose the same HTTPS schema to the app, with actual measurement timestamps and no simulated flag. Sleep needs an appropriate source; soreness and energy remain self-reports. That hardware/vendor integration is not included here.

## Troubleshooting

- 401: tokens differ or are missing.
- 404: no sample has arrived for that exact alias, or the path is incorrect.
- 400: reading values fail validation or simulated:true is missing.
- Network/TLS error: confirm the phone can reach the HTTPS host and trusts its certificate.
- Extension waiting: green flag must run and ReadingSeq must increase.
- No new history: check the model is ready, athlete inclusion is enabled, and the sample timestamp is newer and within the configured age.

Official TurboWarp custom-extension reference:
https://docs.turbowarp.org/development/extensions/unsandboxed
