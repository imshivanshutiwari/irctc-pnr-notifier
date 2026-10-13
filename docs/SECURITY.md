# Security Requirements

- Store API keys and notification credentials only in local ignored env files or GitHub Actions secrets.
- Treat any key previously committed to a public repository as exposed; rotate it with its provider.
- Do not commit `status_state.json`, real PNRs, booking dates, routes, or passenger status.
- Deleting a file from the latest commit does not remove it from Git history. History cleanup requires a separate reviewed operation.
- Mask PNRs in logs; never log API keys or authorization headers.
- Use least-privilege workflow permissions.
- Do not send live booking state to public artifacts or public notification topics.
- Use a private durable store if state must persist between CI runs.
- Minimize retained data and document retention/deletion behavior.
- Treat third-party PNR providers as external dependencies; do not claim unlimited availability or bypass their controls.
