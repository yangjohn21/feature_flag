from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.schema import Base
from app.services.flag_service import FlagService
from app.services.cache import TTLCache


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
    service.set_user_override("beta_feature", user_id=123, enabled=False)
    assert service.evaluate("beta_feature", user_id=123) is False

    session.close()
