# test_main.py
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.append('.')

from main import Config, DownloadHistory, DownloadWorker, validate_url


class TestValidateURL:
    """Testes para validação de URLs"""
    
    def test_valid_youtube_urls(self):
        """Testa URLs válidas do YouTube"""
        is_valid, platform, _ = validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert is_valid
        assert platform == "YouTube"
        
        is_valid, platform, _ = validate_url("https://youtu.be/dQw4w9WgXcQ")
        assert is_valid
        assert platform == "YouTube"
        
        is_valid, platform, _ = validate_url("https://www.youtube.com/playlist?list=PLABC123")
        assert is_valid
        assert platform == "YouTube"
    
    def test_valid_instagram_urls(self):
        """Testa URLs válidas do Instagram"""
        is_valid, platform, _ = validate_url("https://www.instagram.com/p/CxYz123ABC/")
        assert is_valid
        assert platform == "Instagram"
        
        is_valid, platform, _ = validate_url("https://instagram.com/reel/CxYz123ABC")
        assert is_valid
        assert platform == "Instagram"
    
    def test_valid_tiktok_urls(self):
        """Testa URLs válidas do TikTok"""
        is_valid, platform, _ = validate_url("https://www.tiktok.com/@user/video/123456789")
        assert is_valid
        assert platform == "TikTok"
    
    def test_valid_twitter_urls(self):
        """Testa URLs válidas do Twitter"""
        is_valid, platform, _ = validate_url("https://twitter.com/user/status/123456789")
        assert is_valid
        assert platform == "Twitter/X"
        
        is_valid, platform, _ = validate_url("https://x.com/user/status/123456789")
        assert is_valid
        assert platform == "Twitter/X"
    
    def test_invalid_urls(self):
        """Testa URLs inválidas"""
        is_valid, _, error = validate_url("not_a_url")
        assert not is_valid
        assert error is not None
        
        is_valid, _, error = validate_url("ftp://invalid.com")
        assert not is_valid
        
        is_valid, _, error = validate_url("")
        assert not is_valid
    
    def test_url_empty(self):
        """Testa URL vazia"""
        is_valid, _, error = validate_url("   ")
        assert not is_valid
        assert "vazia" in error.lower()

class TestDownloadHistory:
    def test_add_download(self, tmp_path):
        """Testa adição de download ao histórico"""
        with patch('main.HISTORY_FILE', tmp_path / "history.json"):
            history = DownloadHistory()
            history.add_download(
                url="https://youtube.com/test",
                title="Test Video",
                platform="YouTube",
                status="SUCCESS"
            )
            
            assert len(history.history) == 1
            assert history.history[0]['title'] == "Test Video"
            assert history.history[0]['status'] == "SUCCESS"
            assert history.history[0]['platform'] == "YouTube"
    
    def test_load_history_empty(self, tmp_path):
        """Testa carregamento de histórico vazio"""
        with patch('main.HISTORY_FILE', tmp_path / "nonexistent.json"):
            history = DownloadHistory()
            assert history.history == []
    
    def test_history_persistence(self, tmp_path):
        """Testa persistência do histórico"""
        history_file = tmp_path / "history.json"
        with patch('main.HISTORY_FILE', history_file):
            history = DownloadHistory()
            history.add_download("url1", "title1", "YouTube", "SUCCESS")
            history.add_download("url2", "title2", "TikTok", "FAILED")
            
            # Recarrega o histórico
            history2 = DownloadHistory()
            assert len(history2.history) == 2
            assert history2.history[0]['title'] == "title1"
    
    def test_clear_history(self, tmp_path):
        """Testa limpeza do histórico"""
        with patch('main.HISTORY_FILE', tmp_path / "history.json"):
            history = DownloadHistory()
            history.add_download("url1", "title1", "YouTube", "SUCCESS")
            assert len(history.history) == 1
            
            history.clear()
            assert len(history.history) == 0
            
            # Verifica se salvou
            history2 = DownloadHistory()
            assert len(history2.history) == 0

class TestDownloadWorker:
    def test_detect_platform(self):
        """Testa detecção de plataforma"""
        worker = DownloadWorker(None, None, None)
        
        assert worker._detect_platform("https://youtube.com/watch?v=abc") == "YouTube"
        assert worker._detect_platform("https://youtu.be/abc") == "YouTube"
        assert worker._detect_platform("https://tiktok.com/@user/video/123") == "TikTok"
        assert worker._detect_platform("https://instagram.com/p/abc") == "Instagram"
        assert worker._detect_platform("https://twitter.com/user/status/123") == "Twitter/X"
        assert worker._detect_platform("https://x.com/user/status/123") == "Twitter/X"
        assert worker._detect_platform("https://facebook.com/watch/123") == "Facebook"
        assert worker._detect_platform("https://vimeo.com/123") == "Vimeo"
        assert worker._detect_platform("https://soundcloud.com/user/track") == "SoundCloud"
        assert worker._detect_platform("https://twitch.tv/videos/123") == "Twitch"
        assert worker._detect_platform("https://reddit.com/r/test/comments/abc") == "Reddit"
        assert worker._detect_platform("https://unknown.com") == "Site Suportado"

class TestConfig:
    def test_config_load_default(self, tmp_path):
        """Testa carregamento de configuração padrão"""
        with patch('main.CONFIG_FILE', tmp_path / "config.json"):
            config = Config()
            assert config.get('save_dir') is not None
            assert config.get('last_quality') == 'best (recomendado)'
            assert config.get('dark_mode') is True
    
    def test_config_save_and_load(self, tmp_path):
        """Testa salvar e carregar configuração"""
        config_file = tmp_path / "config.json"
        with patch('main.CONFIG_FILE', config_file):
            config = Config()
            config.set('test_key', 'test_value')
            
            # Recarrega
            config2 = Config()
            assert config2.get('test_key') == 'test_value'
    
    def test_config_custom_values(self, tmp_path):
        """Testa valores customizados na configuração"""
        config_file = tmp_path / "config.json"
        with patch('main.CONFIG_FILE', config_file):
            config = Config()
            config.set('last_quality', '1080p')
            config.set('max_history', 50)
            
            assert config.get('last_quality') == '1080p'
            assert config.get('max_history') == 50

if __name__ == "__main__":
    pytest.main(["-v"])