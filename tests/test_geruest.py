from tools import common


def test_kopie_statt_repo(repo):
    assert common.VAULT == repo / "vault"
    assert common.PARTS_CSV.exists()
    assert common.PARTS_CSV.is_relative_to(repo)
    assert any(common.BEREICHE_DIR.glob("*.md"))
