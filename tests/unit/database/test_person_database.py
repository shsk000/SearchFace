import pytest
import tempfile
import os
from src.database.person_database import PersonDatabase


class TestPersonDatabase:
    """PersonDatabase クラスのテストクラス"""

    @pytest.fixture
    def temp_db_path(self):
        """テスト用の一時データベースファイルパスを作成"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            temp_path = temp_file.name
        yield temp_path
        # クリーンアップ
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def person_db(self, temp_db_path):
        """PersonDatabase インスタンスを作成"""
        db = PersonDatabase(temp_db_path)
        yield db
        db.close()

    def test_create_person(self, person_db):
        """人物作成のテスト"""
        # テストデータ
        name = "テスト人物"
        metadata = {"test": "data"}

        # 人物を作成
        person_id = person_db.create_person(name, metadata)

        # 結果を確認
        assert person_id is not None
        assert isinstance(person_id, int)
        assert person_id > 0

    def test_get_person_by_name(self, person_db):
        """名前による人物検索のテスト"""
        # テストデータ
        name = "テスト人物"
        metadata = {"test": "data"}

        # 人物を作成
        created_id = person_db.create_person(name, metadata)

        # 名前で検索
        person = person_db.get_person_by_name(name)

        # 結果を確認
        assert person is not None
        assert person['person_id'] == created_id
        assert person['name'] == name
        assert person['metadata'] == metadata

    def test_get_person_by_name_not_found(self, person_db):
        """存在しない人物名での検索テスト"""
        person = person_db.get_person_by_name("存在しない人物")
        assert person is None

    def test_get_person_by_id(self, person_db):
        """IDによる人物検索のテスト"""
        # テストデータ
        name = "テスト人物"
        metadata = {"test": "data"}

        # 人物を作成
        created_id = person_db.create_person(name, metadata)

        # IDで検索
        person = person_db.get_person_by_id(created_id)

        # 結果を確認
        assert person is not None
        assert person['person_id'] == created_id
        assert person['name'] == name
        assert person['metadata'] == metadata

    def test_get_person_by_id_not_found(self, person_db):
        """存在しない人物IDでの検索テスト"""
        person = person_db.get_person_by_id(999999)
        assert person is None

    def test_get_person_names(self, person_db):
        """複数人物名取得のテスト"""
        # テストデータ
        names = ["人物1", "人物2", "人物3"]
        person_ids = []

        # 複数の人物を作成
        for name in names:
            person_id = person_db.create_person(name)
            person_ids.append(person_id)

        # 名前を取得
        name_mapping = person_db.get_person_names(person_ids)

        # 結果を確認
        assert len(name_mapping) == 3
        for person_id, name in zip(person_ids, names):
            assert name_mapping[person_id] == name

    def test_get_person_names_empty(self, person_db):
        """空のIDリストでの名前取得テスト"""
        name_mapping = person_db.get_person_names([])
        assert name_mapping == {}

    def test_create_person_profile(self, person_db):
        """人物プロフィール作成のテスト"""
        # 人物を作成
        person_id = person_db.create_person("テスト人物")

        # プロフィールを作成
        metadata = {"profile": "test"}

        profile_id = person_db.create_person_profile(person_id, metadata)

        # 結果を確認
        assert profile_id is not None
        assert isinstance(profile_id, int)
        assert profile_id > 0

    def test_get_person_profile(self, person_db):
        """人物プロフィール取得のテスト"""
        # 人物を作成
        person_id = person_db.create_person("テスト人物")

        # プロフィールを作成
        metadata = {"profile": "test"}
        profile_id = person_db.create_person_profile(person_id, metadata)

        # プロフィールを取得
        profile = person_db.get_person_profile(person_id)

        # 結果を確認
        assert profile is not None
        assert profile['profile_id'] == profile_id
        assert profile['person_id'] == person_id
        assert profile['metadata'] == metadata

    def test_get_person_profile_not_found(self, person_db):
        """存在しない人物のプロフィール取得テスト"""
        profile = person_db.get_person_profile(999999)
        assert profile is None

    def test_get_person_detail(self, person_db):
        """人物詳細情報取得のテスト"""
        # 人物を作成
        name = "テスト人物"
        person_id = person_db.create_person(name)

        # プロフィールを作成
        person_db.create_person_profile(person_id)

        # 詳細情報を取得
        detail = person_db.get_person_detail(person_id)

        # 結果を確認
        assert detail is not None
        assert detail['person_id'] == person_id
        assert detail['name'] == name

    def test_get_or_create_person_existing(self, person_db):
        """既存人物の取得テスト"""
        # 人物を作成
        name = "テスト人物"
        original_id = person_db.create_person(name)

        # 同じ名前で get_or_create を呼び出し
        person_id = person_db.get_or_create_person(name)

        # 既存のIDが返されることを確認
        assert person_id == original_id

    def test_get_or_create_person_new(self, person_db):
        """新規人物の作成テスト"""
        # 新しい人物名で get_or_create を呼び出し
        name = "新しい人物"
        metadata = {"new": "person"}

        person_id = person_db.get_or_create_person(name, metadata)

        # 新しい人物が作成されることを確認
        assert person_id is not None

        # 人物情報を確認
        person = person_db.get_person_by_id(person_id)
        assert person['name'] == name
        assert person['metadata'] == metadata

        # プロフィールも作成されることを確認
        profile = person_db.get_person_profile(person_id)
        assert profile is not None

    def test_update_person(self, person_db):
        """人物情報更新のテスト"""
        # 人物を作成
        original_name = "元の名前"
        person_id = person_db.create_person(original_name)

        # 情報を更新
        new_name = "新しい名前"
        new_metadata = {"updated": "data"}

        success = person_db.update_person(person_id, new_name, new_metadata)
        assert success is True

        # 更新された情報を確認
        person = person_db.get_person_by_id(person_id)
        assert person['name'] == new_name
        assert person['metadata'] == new_metadata

    def test_update_person_not_found(self, person_db):
        """存在しない人物の更新テスト"""
        success = person_db.update_person(999999, "新しい名前")
        assert success is False

    def test_delete_person(self, person_db):
        """人物削除のテスト"""
        # 人物を作成
        person_id = person_db.create_person("削除される人物")

        # 削除実行
        success = person_db.delete_person(person_id)
        assert success is True

        # 削除されたことを確認
        person = person_db.get_person_by_id(person_id)
        assert person is None

    def test_delete_person_not_found(self, person_db):
        """存在しない人物の削除テスト"""
        success = person_db.delete_person(999999)
        assert success is False

    def test_get_all_persons(self, person_db):
        """全人物取得のテスト"""
        # テストデータ
        names = ["人物1", "人物2", "人物3"]

        # 複数の人物を作成
        for name in names:
            person_id = person_db.create_person(name)
            # プロフィールも作成
            person_db.create_person_profile(person_id)

        # 全人物を取得
        all_persons = person_db.get_all_persons()

        # 結果を確認
        assert len(all_persons) == 3
        retrieved_names = [person['name'] for person in all_persons]
        assert set(retrieved_names) == set(names)

    def test_update_person_profile(self, person_db):
        """人物プロフィール更新のテスト"""
        # 人物を作成
        person_id = person_db.create_person("テスト人物")

        # 初期プロフィールを作成
        initial_metadata = {"initial": "data", "shared": "original"}
        person_db.create_person_profile(person_id, initial_metadata)

        # プロフィールを更新（実装では完全置き換え）
        update_metadata = {"new": "data", "shared": "updated"}
        success = person_db.update_person_profile(person_id, update_metadata)

        # 更新成功を確認
        assert success is True

        # 更新されたプロフィールを取得
        profile = person_db.get_person_profile(person_id)
        assert profile is not None

        # メタデータが完全に置き換えられていることを確認（実装に合わせる）
        updated_metadata = profile['metadata']
        assert 'initial' not in updated_metadata  # 既存データは置き換えられる
        assert updated_metadata['new'] == "data"      # 新規データ
        assert updated_metadata['shared'] == "updated"  # 更新されたデータ

    def test_update_person_profile_nonexistent(self, person_db):
        """存在しない人物のプロフィール更新テスト"""
        # 人物を作成（プロフィールは作成しない）
        person_id = person_db.create_person("テスト人物")
        metadata = {"auto": "created"}

        # 存在しないプロフィールの更新は失敗する（実装に合わせる）
        success = person_db.update_person_profile(person_id, metadata)
        assert success is False

        # プロフィールが存在しないことを確認
        profile = person_db.get_person_profile(person_id)
        assert profile is None

    def test_upsert_person_profile_new(self, person_db):
        """新規プロフィールのupsertテスト"""
        # 人物を作成
        person_id = person_db.create_person("テスト人物")

        # upsert（新規作成）- metadataはJSON文字列で渡す
        import json
        metadata_value = {"upsert": "new"}
        profile_data = {"metadata": json.dumps(metadata_value)}
        profile_id = person_db.upsert_person_profile(person_id, profile_data)

        # プロフィールが作成されたことを確認
        assert profile_id is not None
        profile = person_db.get_person_profile(person_id)
        assert profile is not None
        assert profile['metadata'] == metadata_value

    def test_upsert_person_profile_existing(self, person_db):
        """既存プロフィールのupsertテスト"""
        # 人物を作成
        person_id = person_db.create_person("テスト人物")

        # 初期プロフィールを作成
        initial_metadata = {"initial": "data"}
        original_profile_id = person_db.create_person_profile(person_id, initial_metadata)

        # upsert（更新）- metadataはJSON文字列で渡す
        import json
        update_metadata_value = {"updated": "data"}
        profile_data = {"metadata": json.dumps(update_metadata_value)}
        profile_id = person_db.upsert_person_profile(person_id, profile_data)

        # 同じprofile_idが返されることを確認
        assert profile_id == original_profile_id

        # メタデータが更新されたことを確認（完全置き換え）
        profile = person_db.get_person_profile(person_id)
        assert profile is not None
        updated_metadata = profile['metadata']
        assert updated_metadata == update_metadata_value  # 完全置き換え

    def test_get_persons_with_base_image(self, person_db):
        """base_image_pathを持つ人物取得のテスト"""
        # テストデータ
        person1_id = person_db.create_person("人物1")
        person2_id = person_db.create_person("人物2")
        person3_id = person_db.create_person("人物3")

        # base_image_pathを設定（直接SQLで更新）
        person_db.cursor.execute(
            "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
            ("http://example.com/image1.jpg", person1_id)
        )
        person_db.cursor.execute(
            "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
            ("http://example.com/image2.jpg", person2_id)
        )
        # person3はbase_image_pathなし
        person_db.conn.commit()

        # base_image_pathを持つ人物を取得
        persons = person_db.get_persons_with_base_image()

        # 結果を確認
        assert len(persons) == 2
        person_ids = [person['person_id'] for person in persons]
        assert person1_id in person_ids
        assert person2_id in person_ids
        assert person3_id not in person_ids

        # URLが正しく取得されることを確認
        for person in persons:
            assert person['base_image_path'] is not None
            assert person['base_image_path'].startswith('http://')

    def test_get_persons_with_base_image_exclude_registered(self, person_db):
        """既に登録済みの人物を除外するテスト"""
        # テストデータ
        person1_id = person_db.create_person("人物1")
        person2_id = person_db.create_person("人物2")

        # base_image_pathを設定
        person_db.cursor.execute(
            "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
            ("http://example.com/image1.jpg", person1_id)
        )
        person_db.cursor.execute(
            "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
            ("http://example.com/image2.jpg", person2_id)
        )
        person_db.conn.commit()

        # person1をface_imagesに登録済みとして追加
        person_db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                image_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        person_db.cursor.execute(
            "INSERT INTO face_images (person_id, image_path, image_hash) VALUES (?, ?, ?)",
            (person1_id, "http://example.com/image1.jpg", "dummy_hash")
        )
        person_db.conn.commit()

        # 登録済み除外で取得
        persons = person_db.get_persons_with_base_image(exclude_registered=True)

        # person1は除外され、person2のみ取得されることを確認
        assert len(persons) == 1
        assert persons[0]['person_id'] == person2_id

    def test_get_persons_with_base_image_with_limit_offset(self, person_db):
        """LIMIT/OFFSETを指定した取得のテスト"""
        # テストデータ（5件）
        person_ids = []
        for i in range(5):
            person_id = person_db.create_person(f"人物{i+1}")
            person_ids.append(person_id)
            person_db.cursor.execute(
                "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
                (f"http://example.com/image{i+1}.jpg", person_id)
            )
        person_db.conn.commit()

        # LIMIT=2で取得
        persons = person_db.get_persons_with_base_image(limit=2)
        assert len(persons) == 2

        # LIMIT=2, OFFSET=2で取得
        persons = person_db.get_persons_with_base_image(limit=2, offset=2)
        assert len(persons) == 2

        # LIMIT=10で取得（実際は5件）
        persons = person_db.get_persons_with_base_image(limit=10)
        assert len(persons) == 5

    def test_get_persons_with_base_image_count(self, person_db):
        """base_image_pathを持つ人物の総数取得のテスト"""
        # 初期状態では0件
        count = person_db.get_persons_with_base_image_count()
        assert count == 0

        # テストデータ
        person1_id = person_db.create_person("人物1")
        person2_id = person_db.create_person("人物2")
        person3_id = person_db.create_person("人物3")

        # 2件にbase_image_pathを設定
        person_db.cursor.execute(
            "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
            ("http://example.com/image1.jpg", person1_id)
        )
        person_db.cursor.execute(
            "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
            ("http://example.com/image2.jpg", person2_id)
        )
        person_db.conn.commit()

        # 総数を確認
        count = person_db.get_persons_with_base_image_count()
        assert count == 2

    def test_get_persons_with_base_image_count_exclude_registered(self, person_db):
        """登録済み除外での総数取得のテスト"""
        # テストデータ
        person1_id = person_db.create_person("人物1")
        person2_id = person_db.create_person("人物2")

        # base_image_pathを設定
        person_db.cursor.execute(
            "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
            ("http://example.com/image1.jpg", person1_id)
        )
        person_db.cursor.execute(
            "UPDATE persons SET base_image_path = ? WHERE person_id = ?",
            ("http://example.com/image2.jpg", person2_id)
        )
        person_db.conn.commit()

        # face_imagesテーブルを作成してperson1を登録済みに
        person_db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                image_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        person_db.cursor.execute(
            "INSERT INTO face_images (person_id, image_path, image_hash) VALUES (?, ?, ?)",
            (person1_id, "http://example.com/image1.jpg", "dummy_hash")
        )
        person_db.conn.commit()

        # 除外なしでは2件
        count = person_db.get_persons_with_base_image_count(exclude_registered=False)
        assert count == 2

        # 除外ありでは1件
        count = person_db.get_persons_with_base_image_count(exclude_registered=True)
        assert count == 1

    def test_get_persons_list_basic(self, person_db):
        """基本的なget_persons_listのテスト"""
        # テストデータを作成
        test_persons = [
            ("テスト女優A", 12345),
            ("テスト女優B", 23456),
            ("テスト女優C", None)
        ]

        for name, dmm_id in test_persons:
            person_id = person_db.create_person(name)
            # DMM IDを設定
            if dmm_id:
                person_db.cursor.execute(
                    "UPDATE persons SET dmm_actress_id = ? WHERE person_id = ?",
                    (dmm_id, person_id)
                )
        person_db.conn.commit()

        # get_persons_listで取得
        result = person_db.get_persons_list(limit=10, offset=0)

        # 結果を確認
        assert len(result) == 3
        # 名前順でソートされることを確認
        names = [person['name'] for person in result]
        assert names == sorted(names)

        # データ構造を確認
        for person in result:
            assert 'person_id' in person
            assert 'name' in person
            assert 'dmm_actress_id' in person
            assert 'base_image_path' in person

    def test_get_persons_list_with_search(self, person_db):
        """検索機能付きget_persons_listのテスト"""
        # テストデータを作成
        test_persons = ["AIKA", "AIKA（三浦あいか）", "愛上みお", "藍芽みずき"]

        for name in test_persons:
            person_db.create_person(name)

        # "AIKA"で検索
        result = person_db.get_persons_list(limit=10, offset=0, search="AIKA")

        # 結果を確認（AIKAを含む名前のみ）
        assert len(result) == 2
        for person in result:
            assert "AIKA" in person['name']

    def test_get_persons_list_with_pagination(self, person_db):
        """ページネーション機能のテスト"""
        # テストデータを作成（5件）
        for i in range(5):
            person_db.create_person(f"テスト女優{i:02d}")

        # 1ページ目（2件）
        result_page1 = person_db.get_persons_list(limit=2, offset=0)
        assert len(result_page1) == 2

        # 2ページ目（2件）
        result_page2 = person_db.get_persons_list(limit=2, offset=2)
        assert len(result_page2) == 2

        # 3ページ目（1件）
        result_page3 = person_db.get_persons_list(limit=2, offset=4)
        assert len(result_page3) == 1

        # 重複がないことを確認
        page1_ids = {person['person_id'] for person in result_page1}
        page2_ids = {person['person_id'] for person in result_page2}
        page3_ids = {person['person_id'] for person in result_page3}

        assert len(page1_ids & page2_ids) == 0
        assert len(page1_ids & page3_ids) == 0
        assert len(page2_ids & page3_ids) == 0

    def test_get_persons_list_sort_options(self, person_db):
        """ソート機能のテスト"""
        # テストデータを作成（時系列を明確にするため少し間隔をあける）
        import time

        person1_id = person_db.create_person("ZZZ女優")  # 名前順では最後
        time.sleep(0.1)
        person2_id = person_db.create_person("AAA女優")  # 名前順では最初
        time.sleep(0.1)
        person3_id = person_db.create_person("MMM女優")  # 名前順では中間

        # 名前順ソート
        result_name = person_db.get_persons_list(sort_by="name")
        names = [person['name'] for person in result_name]
        assert names == ["AAA女優", "MMM女優", "ZZZ女優"]

        # ID順ソート（作成順と同じ）
        result_id = person_db.get_persons_list(sort_by="person_id")
        ids = [person['person_id'] for person in result_id]
        assert ids == [person1_id, person2_id, person3_id]

        # 作成日順ソート
        result_created = person_db.get_persons_list(sort_by="created_at")
        created_ids = [person['person_id'] for person in result_created]
        assert created_ids == [person1_id, person2_id, person3_id]

    def test_get_persons_count_basic(self, person_db):
        """基本的なget_persons_countのテスト"""
        # 初期状態では0件
        count = person_db.get_persons_count()
        assert count == 0

        # テストデータを追加
        for i in range(3):
            person_db.create_person(f"テスト女優{i}")

        # 件数を確認
        count = person_db.get_persons_count()
        assert count == 3

    def test_get_persons_count_with_search(self, person_db):
        """検索機能付きget_persons_countのテスト"""
        # テストデータを作成
        test_persons = ["AIKA", "AIKA（三浦あいか）", "愛上みお", "藍芽みずき"]

        for name in test_persons:
            person_db.create_person(name)

        # 全体の件数
        total_count = person_db.get_persons_count()
        assert total_count == 4

        # "AIKA"で検索した場合の件数
        search_count = person_db.get_persons_count(search="AIKA")
        assert search_count == 2

        # "愛"で検索した場合の件数
        search_count_ai = person_db.get_persons_count(search="愛")
        assert search_count_ai == 1  # "愛上みお"のみ

    def test_get_persons_list_empty_result(self, person_db):
        """空の結果のテスト"""
        # データなしの状態
        result = person_db.get_persons_list()
        assert result == []

        # 検索でヒットしない場合
        person_db.create_person("テスト女優")
        result = person_db.get_persons_list(search="存在しない名前")
        assert result == []

    def test_get_persons_list_with_dmm_actress_id(self, person_db):
        """DMM女優IDが設定されている場合のテスト"""
        # DMM女優IDありの人物を作成
        person_id = person_db.create_person("テスト女優")
        person_db.cursor.execute(
            "UPDATE persons SET dmm_actress_id = ? WHERE person_id = ?",
            (12345, person_id)
        )
        person_db.conn.commit()

        # 取得して確認
        result = person_db.get_persons_list()
        assert len(result) == 1
        assert result[0]['dmm_actress_id'] == 12345
