import pytest

from jaraco.develop import towncrier
from jaraco.versioning import semver


@pytest.mark.parametrize(
    ("file", "expected_version", "title", "show_content"),
    [
        ("1.removal.rst", "v1.0.0", "Removals and Breaking Changes", True),
        ("2.feature.rst", "v0.1.0", "Features", True),
        ("3.deprecation.rst", "v0.1.0", "Deprecations", True),
        ("4.bugfix.rst", "v0.0.1", "Bugfixes", True),
        ("5.doc.rst", "v0.1.0", "Documentation", False),
        ("6.misc.rst", "v0.0.1", "Miscellaneous", False),
    ],
)
def test_release_bumps(
    monkeypatch, tmp_path, git_repo, file, expected_version, title, show_content
):
    monkeypatch.chdir(tmp_path)
    git_repo.commit_tree({}, 'initial commit')
    git_repo._invoke("tag", "v0.0.0")  # from jaraco.vcs.fixtures
    newsfragments = tmp_path / "newsfragments"
    newsfragments.mkdir()
    (newsfragments / file).write_text("Lorem Ipsum", encoding="utf-8")

    towncrier.check_changes()  # no exception
    assert semver(towncrier.get_version()) == expected_version

    news = tmp_path / "NEWS.rst"
    towncrier.run("build", "--yes")
    assert news.is_file()

    content = news.read_text(encoding="utf-8")
    assert expected_version in content
    assert title in content
    assert f"#{file[0]}" in content

    assert show_content == ("Lorem Ipsum" in content)
