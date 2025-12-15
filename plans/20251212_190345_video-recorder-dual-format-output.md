# Plan: Output Both WebM and MP4 Video Formats

## Summary
Modify video_recorder.py to output both .webm (native) and .mp4 (converted) files for every recording.

## Target File
`.claude/skills/playwright-automation/scripts/video_recorder.py`

## Implementation

### Changes to video_recorder.py

1. **Add subprocess import** for ffmpeg execution

2. **Add convert_to_mp4() function**:
   ```python
   def convert_to_mp4(webm_path: str) -> str:
       """Convert WebM to MP4 using ffmpeg."""
       mp4_path = webm_path.replace('.webm', '.mp4')
       logger.info(f"Converting to MP4: {mp4_path}")
       subprocess.run([
           'ffmpeg', '-i', webm_path,
           '-c:v', 'libx264', '-c:a', 'aac',
           '-y', '-loglevel', 'error',
           mp4_path
       ], check=True, capture_output=True)
       return mp4_path
   ```

3. **Modify record_video() return**:
   - After getting webm video_path from Playwright
   - Call convert_to_mp4() to create MP4 copy
   - Keep both files
   - Return tuple: (webm_path, mp4_path)

4. **Update docstring** to reflect dual output

5. **Update print statements** to show both file paths

### Workflow
```
Playwright records → .webm file (kept)
       ↓
ffmpeg converts → .mp4 file (created)
       ↓
Output: Both files saved
```

### Output Example
```
Video saved (WebM): ${CLAUDE_PATH}/.data/playwright/videos/example_20251212.webm
Video saved (MP4):  ${CLAUDE_PATH}/.data/playwright/videos/example_20251212.mp4
```

## TODO
- [x] Add subprocess import
- [x] Add convert_to_mp4() function
- [x] Modify record_video() to create both formats
- [x] Update docstring and output messages
- [ ] Test with `task claude:record URL=https://example.com`
