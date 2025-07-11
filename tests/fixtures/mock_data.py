#!/usr/bin/env python3
"""
テスト用モックデータ
"""

# モックハッシュタグデータ
MOCK_HASHTAG_DATA = {
    "hashtag": "test",
    "url": "https://www.instagram.com/explore/tags/test/",
    "post_count": 1234567,
    "related_tags": ["test1", "test2", "test3", "testing", "testpost"],
    "top_posts": [
        {
            "url": "https://www.instagram.com/p/ABC123/",
            "post_id": "ABC123",
            "image_url": "https://example.com/image1.jpg",
            "type": "image",
            "alt_text": "Test post 1"
        },
        {
            "url": "https://www.instagram.com/p/DEF456/",
            "post_id": "DEF456", 
            "image_url": "https://example.com/image2.jpg",
            "type": "video",
            "alt_text": "Test post 2"
        }
    ],
    "error": None,
    "scraped_at": 1234567890.0
}

# エラー時のハッシュタグデータ
ERROR_HASHTAG_DATA = {
    "hashtag": "errortest",
    "url": "https://www.instagram.com/explore/tags/errortest/",
    "post_count": 0,
    "related_tags": [],
    "top_posts": [],
    "error": "ログインセッションが切れています",
    "scraped_at": 1234567890.0
}

# モックCSVデータ
MOCK_CSV_CONTENT = """hashtag
citywalkhk
japantravel
photography
testtag
"""

# モック設定データ
MOCK_SCHEDULER_CONFIG = {
    "jobs": [
        {
            "name": "test_job",
            "description": "テスト用ジョブ",
            "schedule": "daily",
            "time": "10:00",
            "tags_file": "config/test_tags.csv",
            "enabled": True,
            "headless": True,
            "delay": 2.0
        }
    ],
    "settings": {
        "max_concurrent_jobs": 1,
        "log_retention_days": 7,
        "error_notification": True,
        "success_notification": False
    }
}

# モックHTMLレスポンス
MOCK_HASHTAG_PAGE_HTML = """
<html>
<head><title>Instagram</title></head>
<body>
    <header>
        <span>1,234,567 posts</span>
    </header>
    <div>
        <a href="/explore/tags/test1/">#test1</a>
        <a href="/explore/tags/test2/">#test2</a>
        <a href="/explore/tags/test3/">#test3</a>
    </div>
    <article>
        <a href="/p/ABC123/">
            <img src="https://example.com/image1.jpg" alt="Test post 1">
        </a>
        <a href="/p/DEF456/">
            <img src="https://example.com/image2.jpg" alt="Test post 2">
        </a>
    </article>
</body>
</html>
"""

# モックcookieデータ
MOCK_COOKIES = [
    {
        "name": "sessionid",
        "value": "test_session_id_12345",
        "domain": ".instagram.com",
        "path": "/",
        "secure": True,
        "httpOnly": True
    },
    {
        "name": "csrftoken",
        "value": "test_csrf_token",
        "domain": ".instagram.com",
        "path": "/",
        "secure": True
    }
]