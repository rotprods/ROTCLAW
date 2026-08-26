.PHONY: qa context preflight router recovery
qa:
	python3 scripts/qa.py
	python3 scripts/adversarial.py
context:
	python3 scripts/context_compile.py "$(Q)"
preflight:
	bash context/RUNTIME_PREFLIGHT.sh
router:
	python3 router/model_router.py
recovery:
	python3 scripts/recovery_snapshot.py
