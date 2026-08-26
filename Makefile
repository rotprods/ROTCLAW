.PHONY: qa ancestry config-check context preflight bootstrap router recovery verify-live
ancestry:
	python3 scripts/ancestry_check.py
config-check:
	python3 scripts/config_static_check.py
qa: ancestry config-check
	python3 scripts/qa.py
	python3 scripts/adversarial.py
	python3 scripts/benchmark.py
context:
	python3 scripts/context_compile.py "$(Q)"
preflight:
	bash context/RUNTIME_PREFLIGHT.sh
bootstrap:
	bash scripts/bootstrap-private-env.sh
router:
	bash scripts/run-router.sh
recovery:
	python3 scripts/recovery_snapshot.py
verify-live: ancestry config-check
	bash scripts/verify-live.sh
