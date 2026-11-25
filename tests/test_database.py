from database import Database

def test_welcome_credit_once(tmp_path):
    db=Database(str(tmp_path/"t.sqlite"),200)
    assert db.ensure_user(123,"u","User") is True
    assert db.get_user(123)["credits"]==200
    assert db.ensure_user(123,"u","User") is False
    assert db.get_user(123)["credits"]==200

def test_payment_requires_owner_approval_and_cannot_repeat(tmp_path):
    db=Database(str(tmp_path/"t.sqlite"),200)
    db.ensure_user(123,"u","User")
    pid=db.create_payment(123,99); db.attach_proof(pid,"file")
    assert db.get_user(123)["credits"]==200
    result=db.review_payment(pid,True)
    assert result["credits"]==500
    assert db.get_user(123)["credits"]==700
    assert db.review_payment(pid,True) is None
