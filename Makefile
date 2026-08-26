.PHONY: qa ancestry context preflight router recovery verify-live
ancestry:
	python3 scripts/ancestry_check.py
qa: ancestry
	python3 scripts/qa.py
	python3 scripts/adversarial.py
	python3 scripts/benchmark.py
context:
	python3 scripts/context_compile.py "$(Q)"
preflight:
	bash context/RUNTIME_PREFLIGHT.sh
router:
	python3 router/model_router.py
recovery:
	python3 scripts/recovery_snapshot.py
verify-live: ancestry
	bash scripts/verify-live.sh
