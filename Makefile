.PHONY: qa ancestry config-check promotion context preflight bootstrap router recovery verify-live live-contract live-qualify
ancestry:
	python3 scripts/ancestry_check.py
config-check:
	python3 scripts/config_static_check.py
promotion:
	python3 scripts/promotion_check.py
qa: ancestry config-check promotion
	python3 scripts/qa.py
	python3 scripts/adversarial.py
	python3 scripts/benchmark.py
	python3 scripts/live_qualification.py
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
verify-live: ancestry config-check promotion
	bash scripts/verify-live.sh
live-contract:
	python3 scripts/live_qualification.py
live-qualify: ancestry config-check promotion
	python3 scripts/live_qualification.py --live
