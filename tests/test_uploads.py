from conftest import image_bytes, upload


def test_image_upload_creates_thumbnail(client, admin):
    res = upload(client, admin, image_bytes("JPEG"))
    assert res["file_type"] == "image" and res["url"].endswith(".jpg")
    assert res["thumb_url"].startswith("/media/thumbs/")
    assert client.get(res["url"]).status_code == 200


def test_fake_and_corrupt_files_rejected(client, admin):
    r = client.post("/admin/uploads", headers=admin, files={"file": ("x.png", b"not an image")})
    assert r.status_code == 400
    broken = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # sarlavha to'g'ri, ichi buzuq
    r = client.post("/admin/uploads", headers=admin, files={"file": ("x.png", broken)})
    assert r.status_code == 400


def test_upload_requires_admin(client, user):
    r = client.post("/admin/uploads", headers=user, files={"file": ("a.png", image_bytes())})
    assert r.status_code == 403


def test_pdf_is_private_but_admin_can_view(client, admin, user, make_pattern):
    pdf = upload(client, admin, b"%PDF-1.4 maxfiy", "a.pdf")
    assert pdf["url"].startswith("private/")
    assert client.get(f"/media/{pdf['url'].split('/')[-1]}").status_code == 404

    p = make_pattern()
    f = client.post(f"/admin/patterns/{p['id']}/files", headers=admin,
                    json={"url": pdf["url"], "kind": "download", "file_type": "pdf"}).json()
    url = f"/admin/patterns/{p['id']}/files/{f['id']}/content"
    r = client.get(url, headers=admin)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content == b"%PDF-1.4 maxfiy"
    assert client.get(url, headers=user).status_code == 403


def test_file_url_must_come_from_uploads(client, admin, make_clothes, make_pattern):
    c = make_clothes()
    for bad in ("https://evil.example/x.png", "private/abc.pdf", "/media/../../.env"):
        r = client.post(f"/admin/clothes/{c['id']}/images", headers=admin, json={"url": bad})
        assert r.status_code == 422, bad

    p = make_pattern()
    img = upload(client, admin, image_bytes())
    # rasmni "download" sifatida yoki PDF'ni "preview" sifatida berib bo'lmaydi
    r = client.post(f"/admin/patterns/{p['id']}/files", headers=admin,
                    json={"url": img["url"], "kind": "download", "file_type": "image"})
    assert r.status_code == 422
