def test_guest_can_list_but_not_create(client, user):
    assert client.get("/genders").status_code == 200
    assert client.post("/tags", json={"name": "Yozgi"}).status_code in (401, 403)
    assert client.post("/tags", headers=user, json={"name": "Yozgi"}).status_code == 403


def test_tag_slug_cyrillic_and_stable_on_rename(client, admin):
    tag = client.post("/tags", headers=admin, json={"name": "Қишки кийим"}).json()
    assert tag["slug"] == "qishki-kiyim"
    renamed = client.put(f"/tags/{tag['id']}", headers=admin, json={"name": "Qishki"}).json()
    assert renamed["name"] == "Qishki" and renamed["slug"] == "qishki-kiyim"


def test_duplicate_tag_name_409_but_reusable_after_delete(client, admin):
    tag = client.post("/tags", headers=admin, json={"name": "Yozgi"}).json()
    assert client.post("/tags", headers=admin, json={"name": "Yozgi"}).status_code == 409
    assert client.delete(f"/tags/{tag['id']}", headers=admin).status_code == 204
    again = client.post("/tags", headers=admin, json={"name": " Yozgi "})
    assert again.status_code == 201
    assert again.json()["name"] == "Yozgi"  # bo'shliqlar kesiladi


def test_used_gender_season_tag_cannot_be_deleted(client, admin, make_clothes, make_pattern):
    tag = client.post("/tags", headers=admin, json={"name": "Klassik"}).json()
    clothes = make_clothes(gender_id=2, season_id=2, tag_ids=[tag["id"]])
    make_pattern(tag_ids=[tag["id"]])

    for url in ("/genders/2", "/seasons/2", f"/tags/{tag['id']}"):
        r = client.delete(url, headers=admin)
        assert r.status_code == 409, url
        assert "ishlatilmoqda" in r.json()["detail"]

    # kiyim o'chirilgach jins va fasl bo'shaydi (teg hali patternda)
    client.delete(f"/admin/clothes/{clothes['id']}", headers=admin)
    assert client.delete("/genders/2", headers=admin).status_code == 204
    assert client.delete("/seasons/2", headers=admin).status_code == 204
    assert client.delete(f"/tags/{tag['id']}", headers=admin).status_code == 409


def test_delete_missing_category_404(client, admin):
    assert client.delete("/genders/999", headers=admin).status_code == 404
