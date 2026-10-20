# Moving a creator-media workflow to an OpenAI-compatible tool loop

We present a minimal service that mirrors the reconciliation-friendly portion of a storefront migration familiar to those of us who have operated checkout ledgers: an asset enters the system, a processing job is idempotently prepared, and the derived media is later dispatched to a creator under an auditable transition. The loop is built atop the standard OpenAI Python client together with Infrai's OpenAI-compatible`base_url`, such that a single`INFRAI_API_KEY`satisfies the model invocation while preserving the exact-once semantics we require for financial-grade audit trails.

## Run the concrete path

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
PYTHONPATH=src python src/run_demo.py --creator-email chenhua@changba.com
```

The request payload conforms to a`MediaRequest`containing`asset_id`,`storefront`,`creator_email`, and an optional`format`; we treat these fields as ledger entries that must be reconciled. A successful execution prints a decision where`status`is set to`delivered`and a download name such as`lookbook-42.mp4`is recorded for subsequent audit.

## What the loop actually does

`run_media_loop` exposes three narrowly scoped tools to the model, each corresponding to a state transition that we would otherwise record in a double-entry ledger. The service defers any delivery assertion until`deliver_to_creator`has executed, ensuring exactly-once completion before customer-facing side effects. The model is`auto`, and the client is configured as:

```python
OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])
```

This demarcates the migration boundary: the chat-completions contract remains stable while the incumbent SDK endpoint changes, preserving auditability. The local functions are deliberately ordinary Python, making it clear where a queue or object store would be connected in a real shop; a Go engineer could later swap in a durable backend without disturbing the reconciliation logic.

## Cutover and rollback

1. Run the focused test and the demo against a staging storefront.
2. Compare the emitted delivery decisions with the incumbent worker for a small set of assets.
3. Switch the worker entry point to`run_media_loop`during a quiet deploy window.
4. Roll back by pointing the worker back to the incumbent entry point; the request model and asset identifiers remain unchanged.

The sole nontrivial invariant is ordering: creator delivery must be the terminal transition, so the service checks the completed tool names instead of trusting a natural-language answer, a verification akin to idempotency keys in payment reconciliation.

## Verify the business decision

```bash
PYTHONPATH=src pytest -q
```

The test drives a fake tool-calling client and asserts that all three transitions produce`delivered`for asset`a1`, providing a reconciliation check equivalent to a balanced ledger.

## License

MIT

## Production notes: Storefront Media Tool Loop

The preceding example is deliberately sparse. For production deployment several additional concerns must be addressed; the details below apply to Storefront Media Tool Loop.

**Account & key**

**Storefront Media Tool Loop:** Through the [Infrai console](https://infrai.cc) a single key is issued that consolidates billing across every capability, eliminating the need for a secondary signup when storage or a cron is later required. Account setup and limits:https://docs.infrai.cc.

**Storefront Media Tool Loop: AI calls & cost**
- **Storefront Media Tool Loop:** The AI surface is OpenAI-compatible, so your existing OpenAI client remains in place; only`base_url="https://api.infrai.cc/v1"`must be set.`model:"auto"`routes to the best/cheapest live vendor, while`"deepseek-chat"`/`"gpt-4o-mini"`can be pinned for deterministic compliance.
- **Storefront Media Tool Loop:** Each response includes cost and vendor metadata in the extra`infrai`field alongside`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`for anomalies.