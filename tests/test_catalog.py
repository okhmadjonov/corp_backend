from conftest import image_bytes, upload


def test_admin_endpoints_need_admin_role(client, user):
    assert client.get("/admin/clothes").status_code in (401, 403)
    assert client.get("/admin/clothes", headers=user).status_code == 403
    assert client.get("/admin/users", headers=user).status_code == 403


def test_admin_list_is_paginated(client, admin, make_clothes):
    for i in range(3):
        make_clothes(name=f"Kiyim {i}")
    page = client.get("/admin/clothes?limit=2", headers=admin).json()
    assert page["total"] == 3 and len(page["items"]) == 2


def test_slug_and_sku_reusable_after_soft_delete(client, admin, make_clothes):
    c1 = make_clothes(name="Palto")
    variant = {"size": "M", "color": "Qora", "price": "100000", "sku": "P-M"}
    assert client.post(f"/admin/clothes/{c1['id']}/variants", headers=admin, json=variant).status_code == 201
    c2 = make_clothes(name="Palto")
    assert c2["slug"] == "palto-2"
    # tirik variantlar orasida SKU noyob
    assert client.post(f"/admin/clothes/{c2['id']}/variants", headers=admin, json=variant).status_code == 409

    # kiyim o'chirilsa, uning variantlari ham o'chadi va SKU bo'shaydi
    client.delete(f"/admin/clothes/{c1['id']}", headers=admin)
    assert client.post(f"/admin/clothes/{c2['id']}/variants", headers=admin, json=variant).status_code == 201
    assert make_clothes(name="Palto")["slug"] == "palto"  # o'chirilgan slug bo'shadi


def test_catalog_lists_only_active_and_filters(client, admin, make_clothes):
    make_clothes(name="Faol palto", gender_id=1)
    make_clothes(name="Nofaol", is_active=False)
    make_clothes(name="Erkaklar kurtkasi", gender_id=2)

    assert client.get("/clothes").json()["total"] == 2
    assert client.get("/clothes?gender_id=2").json()["items"][0]["name"] == "Erkaklar kurtkasi"
    assert client.get("/clothes?q=palto").json()["total"] == 1


def test_search_escapes_like_wildcards(client, make_clothes):
    make_clothes(name="Palto")
    make_clothes(name="Chegirma 50%")
    assert client.get("/clothes", params={"q": "%"}).json()["total"] == 1
    assert client.get("/clothes", params={"q": "_"}).json()["total"] == 0


def test_tag_filter_ignores_deleted_tag(client, admin, make_clothes):
    tag = client.post("/tags", headers=admin, json={"name": "Yozgi"}).json()
    make_clothes(tag_ids=[tag["id"]])
    assert client.get("/clothes?tag=yozgi").json()["total"] == 1


def test_detail_requires_login_and_counts_views(client, user, make_clothes):
    c = make_clothes(name="Ko'ylak")
    assert client.get(f"/clothes/{c['slug']}").status_code in (401, 403)
    client.get(f"/clothes/{c['slug']}", headers=user)
    detail = client.get(f"/clothes/{c['slug']}", headers=user).json()
    assert detail["views_count"] == 2


def test_inactive_detail_404(client, user, make_clothes):
    c = make_clothes(is_active=False)
    assert client.get(f"/clothes/{c['slug']}", headers=user).status_code == 404


def test_cards_have_thumbnails(client, admin, make_clothes):
    c = make_clothes()
    img = upload(client, admin, image_bytes())
    client.post(f"/admin/clothes/{c['id']}/images", headers=admin,
                json={"url": img["url"], "is_main": True})
    card = client.get("/clothes").json()["items"][0]
    assert card["main_image"] == img["url"]
    assert card["main_thumb"].startswith("/media/thumbs/")
    assert client.get(card["main_thumb"]).status_code == 200


def test_pattern_detail_hides_download_files(client, admin, user, make_pattern):
    p = make_pattern()
    img = upload(client, admin, image_bytes())
    pdf = upload(client, admin, b"%PDF-1.4 test", "a.pdf")
    client.post(f"/admin/patterns/{p['id']}/files", headers=admin,
                json={"url": img["url"], "kind": "preview", "file_type": "image"})
    client.post(f"/admin/patterns/{p['id']}/files", headers=admin,
                json={"url": pdf["url"], "kind": "download", "file_type": "pdf"})
    files = client.get(f"/patterns/{p['slug']}", headers=user).json()["files"]
    assert [f["kind"] for f in files] == ["preview"]


def test_favorites_flow(client, admin, user, make_clothes, make_pattern):
    c = make_clothes()
    p = make_pattern()
    assert client.put(f"/favorites/clothes/{c['id']}", headers=user).status_code == 204
    assert client.put(f"/favorites/patterns/{p['id']}", headers=user).status_code == 204
    ids = client.get("/favorites", headers=user).json()
    assert ids == {"clothes_ids": [c["id"]], "pattern_ids": [p["id"]]}

    # nofaol qilingan mahsulot sevimlilarda ko'rinmaydi
    body = {"name": c["name"], "gender_id": 1, "season_id": 1, "is_active": False}
    client.put(f"/admin/clothes/{c['id']}", headers=admin, json=body)
    assert client.get("/favorites", headers=user).json()["clothes_ids"] == []
    assert client.get("/favorites/clothes", headers=user).json() == []
