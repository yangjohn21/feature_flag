from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.schema import Base
from app.services.flag_service import FlagService
from app.services.cache import TTLCache
from app.services.override_service import OverrideService
import os
import time


def setup_in_memory_db():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal


def test_create_and_evaluate_flag():
    Session = setup_in_memory_db()
    session = Session()
    cache = TTLCache()
    service = FlagService(session=session, cache=cache)

    # create a flag default disabled
    flag = service.create_flag("beta_feature", "A beta feature", default_enabled=False)
    assert flag.name == "beta_feature"

    # evaluate for anon -> default
    assert service.evaluate("beta_feature") is False

    # enable globally
    service.set_global("beta_feature", True)
    assert service.evaluate("beta_feature") is True

    # set user override to false
    OverrideService(session=session, cache=cache).set_user_override("beta_feature", user_id=123, enabled=False)
    assert service.evaluate("beta_feature", user_id=123) is False

    session.close()


def test_create_update_and_list_flag():
    Session = setup_in_memory_db()
    session = Session()
    cache = TTLCache()
    service = FlagService(session=session, cache=cache)

    # create a flag default disabled
    name = "global_feature"
    flag = service.create_flag(name, "A globally toggled feature", default_enabled=False)
    assert flag.default_enabled is False

    # initially evaluates to default (disabled)
    assert service.evaluate(name) is False

    # enable globally
    service.set_global(name, True)

    # list all flags and assert this flag is now globally enabled
    flags = service.list_flags()
    matched = [f for f in flags if f.name == name]
    assert matched, "created flag not found in list_flags()"
    assert matched[0].global_enabled is True

    session.close()


def test_eval_cache_invalidation_on_global_change():
    Session = setup_in_memory_db()
    session = Session()
    cache = TTLCache()
    service = FlagService(session=session, cache=cache)

    name = "cache_feature"
    service.create_flag(name, "cache test", default_enabled=False)

    # warm the evaluation cache
    assert service.evaluate(name) is False
    assert cache.get(f"eval:{name}:anon") is False

    # change global and ensure cache was invalidated
    service.set_global(name, True)
    assert cache.get(f"eval:{name}:anon") is None
    assert service.evaluate(name) is True

    session.close()


def test_user_override_invalidation():
    Session = setup_in_memory_db()
    session = Session()
    cache = TTLCache()
    service = FlagService(session=session, cache=cache)

    name = "user_override"
    service.create_flag(name, "user override test", default_enabled=False)

    # enable globally so default would be True
    service.set_global(name, True)
    assert service.evaluate(name) is True

    # set user override to False and ensure evaluation and cache reflect it
    OverrideService(session=session, cache=cache).set_user_override(name, user_id=42, enabled=False)
    assert service.evaluate(name, user_id=42) is False
    assert cache.get(f"eval:{name}:42") is False

    # flip override to True and ensure cache invalidation for that user
    OverrideService(session=session, cache=cache).set_user_override(name, user_id=42, enabled=True)
    assert cache.get(f"eval:{name}:42") is None
    assert service.evaluate(name, user_id=42) is True

    session.close()
