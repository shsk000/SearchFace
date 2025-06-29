import pytest
from src.api.models.response import PersonDetailResponse


class TestPersonDetailResponse:
    """PersonDetailResponseモデルのテストクラス"""

    def test_person_detail_response_with_dmm_list_url_digital(self):
        """dmm_list_url_digitalフィールドありのPersonDetailResponseテスト"""
        dmm_url = "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2F"
        response = PersonDetailResponse(
            person_id=1,
            name="テスト女優",
            image_path="test.jpg",
            search_count=10,
            dmm_list_url_digital=dmm_url
        )
        
        assert response.person_id == 1
        assert response.name == "テスト女優"
        assert response.image_path == "test.jpg"
        assert response.search_count == 10
        assert response.dmm_list_url_digital == dmm_url

    def test_person_detail_response_without_dmm_list_url_digital(self):
        """dmm_list_url_digitalフィールドなしのPersonDetailResponseテスト"""
        response = PersonDetailResponse(
            person_id=1,
            name="テスト女優",
            image_path="test.jpg",
            search_count=10
        )
        
        assert response.person_id == 1
        assert response.name == "テスト女優"
        assert response.image_path == "test.jpg"
        assert response.search_count == 10
        assert response.dmm_list_url_digital is None

    def test_person_detail_response_with_none_dmm_list_url_digital(self):
        """dmm_list_url_digitalフィールドがNoneの場合のテスト"""
        response = PersonDetailResponse(
            person_id=1,
            name="テスト女優",
            image_path="test.jpg",
            search_count=10,
            dmm_list_url_digital=None
        )
        
        assert response.person_id == 1
        assert response.name == "テスト女優"
        assert response.image_path == "test.jpg"
        assert response.search_count == 10
        assert response.dmm_list_url_digital is None

    def test_person_detail_response_json_serialization(self):
        """JSON シリアライゼーションテスト"""
        dmm_url = "https://al.dmm.co.jp/?lurl=https%3A%2F%2Fwww.dmm.co.jp%2F"
        response = PersonDetailResponse(
            person_id=1,
            name="テスト女優",
            image_path="test.jpg",
            search_count=10,
            dmm_list_url_digital=dmm_url
        )
        
        json_data = response.model_dump()
        assert "dmm_list_url_digital" in json_data
        assert json_data["dmm_list_url_digital"] == dmm_url
        assert json_data["person_id"] == 1
        assert json_data["name"] == "テスト女優"
        assert json_data["image_path"] == "test.jpg"
        assert json_data["search_count"] == 10

    def test_person_detail_response_json_serialization_without_dmm_url(self):
        """dmm_list_url_digitalなしの場合のJSON シリアライゼーションテスト"""
        response = PersonDetailResponse(
            person_id=1,
            name="テスト女優",
            image_path="test.jpg",
            search_count=10
        )
        
        json_data = response.model_dump()
        assert "dmm_list_url_digital" in json_data
        assert json_data["dmm_list_url_digital"] is None
        assert json_data["person_id"] == 1
        assert json_data["name"] == "テスト女優"
        assert json_data["image_path"] == "test.jpg"
        assert json_data["search_count"] == 10

    def test_person_detail_response_empty_string_dmm_list_url_digital(self):
        """dmm_list_url_digitalが空文字列の場合のテスト"""
        response = PersonDetailResponse(
            person_id=1,
            name="テスト女優",
            image_path="test.jpg",
            search_count=10,
            dmm_list_url_digital=""
        )
        
        assert response.dmm_list_url_digital == ""