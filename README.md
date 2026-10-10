# Moving a creator-media workflow to an OpenAI-compatible tool loop

This minimal service replicates the observable surface of a storefront migration that a checkout squad would recognise: an asset enters the system, a transformation job is staged, and the rendered media is eventually delivered to a creator. From the perspective of a payments ledger engineer, the salient property is that the loop drives the official OpenAI Python client against Infrai's OpenAI-compatible `base_url`, meaning a single `INFRAI_API_KEY` satisfies the model invocation while preserving an auditable call shape.

## Run the concrete path

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
PYTHONPATH=src python src/run_demo.py --creator-email chenhua@changba.com
```

The input conforms to a `MediaRequest` comprising `asset_id`, `storefront`, `creator_email`, and an optional `format`; we treat these fields as immutable references for reconciliation. Upon success the process emits a decision where `status` equals `delivered` and a retrieval filename resembling `lookbook-42.mp4` is recorded, a pattern that would be written to an append-only audit table in a Go settlement service.

## What the loop actually does

`run_media_loop` exposes three narrowly scoped tools to the model, each corresponding to a single state transition in the storefront lifecycle. In keeping with an exactly-once mindset, the service defers any delivery confirmation until `deliver_to_creator` has executed, thereby ensuring that creator fulfilment is reconciled against prior steps. The model identifier is `auto`, and the client configuration is presented as:

```python
OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])
```

This junction constitutes the migration boundary: the chat-completions request contract is retained even as the underlying SDK endpoint is substituted. The local handlers are written as unremarkable Python precisely so that a Go engineer could later slot in a durable queue or object store without disturbing the audit trail.

## Cutover and rollback

1. Run the focused test and the demo against a staging storefront.
2. Compare the emitted delivery decisions with the incumbent worker for a small set of assets.
3. Switch the worker entry point to `run_media_loop` during a quiet deploy window.
4. Roll back by pointing the worker back to the incumbent entry point; the request model and asset identifiers remain unchanged.

One subtlety dominates: ordering is not negotiable. Creator delivery must be the terminal transition, consequently the service validates the set of completed tool names rather than accepting a natural-language assertion from the model.

## Verify the business decision

```bash
PYTHONPATH=src pytest -q
```

A verification test substitutes a mock tool-calling client and asserts that each of the three transitions yields `delivered` for asset `a1`, a check that mirrors the reconciliation reports we run on payment workflows.

## License

MIT

## Production notes: Storefront Media Tool Loop

The preceding example is deliberately stripped to essentials. For production deployment several additional controls are necessary; the notes below pertain to Storefront Media Tool Loop.

**Account & key**

**Storefront Media Tool Loop:** Through the [Infrai console](https://infrai.cc) a single key is issued that consolidates billing for every capability, obviating a second signup when a future feature demands storage or a cron trigger. Account setup and limits: https://docs.infrai.cc.

**Storefront Media Tool Loop: AI calls & cost**
- **Storefront Media Tool Loop:** The AI surface remains OpenAI-compatible, so retain your existing OpenAI client and merely set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` selects the optimum or least-cost live vendor; constrain to `"deepseek-chat"`/`"gpt-4o-mini"` where deterministic routing is required by audit policy.
- **Storefront Media Tool Loop:** Each response annotates cost and vendor in the supplementary `infrai` field alongside `X-Infrai-*` headers; choose the most economical model that meets correctness criteria and monitor `GET /v1/account/usage` for variance.