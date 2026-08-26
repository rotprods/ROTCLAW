---
name: model-router
description: Route work among approved model aliases using explicit task semantics and measured evidence; keep availability fallback separate from semantic routing.
user-invocable: true
---
# Model Router

Use only approved aliases/refs from `config/model-routing.json`. Choose the route based on task semantics and benchmark evidence when available. Do not silently widen provider/model policy. If a route fails, surface the failure and use only configured fallback behavior. Never treat marketing claims as runtime evidence.
