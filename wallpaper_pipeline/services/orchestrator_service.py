import os
import time
import uuid
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

from config.settings import Config


class WallpaperOrchestratorService:
    def __init__(self, gemini_service, veo_service):
        self.gemini_service = gemini_service
        self.veo_service = veo_service
        os.makedirs(Config.BATCH_SOURCE_FOLDER, exist_ok=True)
        os.makedirs(Config.GENERATED_VIDEO_FOLDER, exist_ok=True)

    def _infer_extension(self, image_url: str, content_type: Optional[str]) -> str:
        if content_type:
            if "png" in content_type:
                return ".png"
            if "webp" in content_type:
                return ".webp"
            if "jpeg" in content_type or "jpg" in content_type:
                return ".jpg"

        parsed = urlparse(image_url)
        extension = os.path.splitext(parsed.path)[1].lower()
        if extension in {".jpg", ".jpeg", ".png", ".webp"}:
            return extension
        return ".jpg"

    def _download_image(self, image_url: str, index: int) -> str:
        response = requests.get(
            image_url,
            stream=True,
            timeout=45,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            },
        )
        response.raise_for_status()

        extension = self._infer_extension(image_url, response.headers.get("content-type"))
        filename = f"pinterest_{index}_{int(time.time())}_{uuid.uuid4().hex[:8]}{extension}"
        file_path = os.path.join(Config.BATCH_SOURCE_FOLDER, filename)

        with open(file_path, "wb") as file_handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_handle.write(chunk)

        return file_path

    def process_image_urls(self, image_urls: List[str], duration: Optional[int] = None) -> Dict:
        if not image_urls:
            return {
                "success": False,
                "error": "At least one image URL is required",
                "results": [],
                "total": 0,
                "generated_count": 0,
                "failed_count": 0,
            }

        duration = duration or Config.VIDEO_DURATION
        results = []

        for index, image_url in enumerate(image_urls):
            item_result = {
                "index": index,
                "source_url": image_url,
                "success": False,
            }

            local_image_path = None

            try:
                local_image_path = self._download_image(image_url, index)
                analysis_result = self.gemini_service.analyze_deity_image(local_image_path)

                if not analysis_result.get("success"):
                    item_result["error"] = analysis_result.get("error", "Image analysis failed")
                    results.append(item_result)
                    continue

                video_result = self.veo_service.generate_video_from_prompt(
                    prompt=analysis_result["animation_prompt"],
                    image_path=local_image_path,
                    duration=duration,
                )

                if not video_result.get("success"):
                    item_result["error"] = video_result.get("error", "Video generation failed")
                    results.append(item_result)
                    continue

                item_result.update(
                    {
                        "success": True,
                        "analysis": analysis_result.get("analysis"),
                        "image_prompt": analysis_result.get("image_prompt"),
                        "animation_prompt": analysis_result.get("animation_prompt"),
                        "video_url": video_result.get("video_url"),
                        "video_path": video_result.get("video_path"),
                        "status": video_result.get("status"),
                        "duration": video_result.get("duration"),
                    }
                )
            except Exception as error:
                item_result["error"] = str(error)
            finally:
                if local_image_path and os.path.exists(local_image_path):
                    try:
                        os.remove(local_image_path)
                    except OSError:
                        pass

            results.append(item_result)

        generated_count = len([result for result in results if result.get("success")])
        failed_count = len(results) - generated_count

        return {
            "success": generated_count > 0,
            "results": results,
            "total": len(results),
            "generated_count": generated_count,
            "failed_count": failed_count,
        }