"""Official SDK Responses adapter; no SDK objects escape this boundary."""

import json

from venuebite.ai import AIError, DEFAULT_MODEL, INSTRUCTIONS, RESPONSE_SCHEMA, bounded_int, unique_json


class OpenAIProvider:
    def __init__(self, api_key="", *, model=DEFAULT_MODEL, timeout=25, max_output_tokens=1400, client=None):
        self.enabled = bool(api_key) or client is not None
        self._api_key, self._client = api_key, client
        self.model = model if isinstance(model, str) and 0 < len(model) <= 100 and all(c.isalnum() or c in "-._" for c in model) else DEFAULT_MODEL
        self.timeout = bounded_int(timeout, 25, 1, 45)
        self.max_output_tokens = bounded_int(max_output_tokens, 1400, 256, 2000)

    def answer(self, context, question, history):
        if not self.enabled:
            raise AIError("not_configured", "The server AI provider is not configured.", 503)
        try:
            from openai import OpenAI, APITimeoutError, RateLimitError, AuthenticationError, APIError
            if self._client is None:
                from openai import DefaultHttpxClient
                self._client = OpenAI(api_key=self._api_key, base_url="https://api.openai.com/v1", timeout=self.timeout,
                                      max_retries=0, http_client=DefaultHttpxClient(follow_redirects=False, trust_env=False))
            response = self._client.responses.create(
                model=self.model, instructions=INSTRUCTIONS,
                input=[{"role": "user", "content": json.dumps({"server_context": context, "question": question,
                         "recent_conversation_data": history}, ensure_ascii=False, allow_nan=False, separators=(",", ":"))}],
                text={"format": {"type": "json_schema", "name": "venuebite_analyst", "strict": True, "schema": RESPONSE_SCHEMA}},
                tools=[], tool_choice="none", store=False, stream=False,
                max_output_tokens=self.max_output_tokens, timeout=self.timeout,
            )
            if response.status != "completed" or any(getattr(part, "type", "") == "refusal" for item in response.output for part in getattr(item, "content", [])):
                raise AIError("incomplete_response", "The analyst could not complete a grounded answer. Try a shorter question.", 502)
            return unique_json(response.output_text)
        except AIError:
            raise
        except APITimeoutError:
            raise AIError("timeout", "The analyst took too long. Please try again.", 504) from None
        except RateLimitError:
            raise AIError("provider_rate_limited", "The AI provider is busy or its usage limit was reached. Try later.", 429) from None
        except AuthenticationError:
            raise AIError("provider_configuration", "The server AI provider configuration needs attention.", 503) from None
        except APIError:
            raise AIError() from None
        except Exception:
            raise AIError("invalid_response", "The analyst could not complete a supported answer.", 502) from None
