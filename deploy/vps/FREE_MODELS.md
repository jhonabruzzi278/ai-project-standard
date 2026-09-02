# OpenRouter free models policy

Hermes uses `openrouter/free` instead of pinning one promotional model. The router filters the current free pool for required request features such as tool calling and structured output, then selects an available model.

Benefits:

- No prompt or completion token charge for requests routed to free variants.
- No need to track changing promotional model slugs.
- Automatic capability filtering for tool-based agent requests.

Limitations:

- Model selection is not deterministic.
- Free availability and model membership change frequently.
- Accounts without at least USD 10 in purchased credits are generally limited to 50 free-model requests per day; qualifying accounts receive a higher daily limit under OpenRouter's current policy.
- Free endpoints can be rate-limited or unavailable during demand peaks.
- Some free providers may use inputs and outputs for model improvement. `provider_routing.data_collection: deny` is therefore mandatory for this project pack.

Do not send `.env`, credentials, private keys, production database exports, customer records or other secrets to any model. Hermes detects secret filenames without opening their contents.
