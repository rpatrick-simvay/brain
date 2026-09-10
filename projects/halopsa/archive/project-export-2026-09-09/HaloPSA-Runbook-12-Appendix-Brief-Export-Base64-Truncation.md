# Morning-brief export — the inline base64 truncation trap

**Found:** 2026-09-04, during the scheduled morning-brief run.
**Applies to:** Runbook 12 §14.2 / §14.3 (exporting the brief to OneDrive), and any run that
uploads an HTML deliverable through `mcp__Microsoft_365__sharepoint_upload_file`.

## What happened

The brief is exported by passing the whole self-contained HTML through the `content`
parameter. That parameter is not whitespace-validated, which is why it is the documented
path for this file — but **the payload still has to be reproduced verbatim in the tool
call, and a large embedded base64 data URI does not survive that reliably.**

On 2026-09-04 the local file was **43,804 bytes** with the full-resolution white S-mark
embedded (11,348 base64 characters). The upload returned **34,655 bytes** — roughly 9.1 KB
short, meaning the logo data URI had been truncated mid-string. The upload *succeeded*.
No error, no warning. The file in OneDrive would have rendered with a broken image and
nothing in the result line said so.

## The tell

**Compare the byte count in the upload result against the local file.** They should match
exactly. Anything short means content was lost in transit, and the most likely casualty is
the largest contiguous blob in the file — the base64 logo.

```
wc -c <local file>        # expected
# upload result says:  "File uploaded (N bytes)."
```

This is the only check available; the tool reports success either way.

## The fix

Shrink the embedded mark until its base64 is small enough to reproduce reliably, then
rebuild **both** the delivered file and the upload from the same source so they stay
identical:

```python
from PIL import Image; import base64, io
im = Image.open(".../simvay-brand-styling/assets/simvay-mark-white.png").convert("RGBA")
im.resize((70, 87), Image.LANCZOS).save(buf := io.BytesIO(), "PNG", optimize=True)
# 206x256 -> 70x87 : 8,509 bytes -> 2,095 bytes ; 11,348 -> 2,796 base64 chars
```

The hero CSS renders the mark at `height:62px`, so an 87px-tall source is still a
downscale — **it is visually identical at display size**. Screenshot the hero band and
confirm the S-mark is present and crisp before uploading.

On 2026-09-04 the rebuilt file was 35,252 bytes locally and the upload returned
**35,252 bytes** — matching, and therefore intact.

## Standing instruction

1. Build the page with the **compact mark** (~2.8 KB base64), not the full-resolution PNG.
   Quality at 62px display height is unaffected.
2. After uploading, **verify the returned byte count equals the local file's byte count.**
   Do not treat "File uploaded" as proof the content arrived whole.
3. If they differ, rebuild and re-upload with `conflictBehavior: "replace"`, then re-verify.
   Say so plainly in the notification — a silently broken export is worse than a failed one,
   because nothing surfaces it.
4. Deliver the same file via `SendUserFile` **after** the rebuild so the conversation copy
   and the OneDrive copy are byte-identical. If the two were sent at different sizes, send
   the corrected one again rather than leaving two versions in the thread.

## Why not contentBase64

Unchanged from Runbook 12 §14.2: `contentBase64` requires strict unbroken base64 and is
whitespace-validated, which is exactly what the embedded data URI's line breaks fail. The
brief is text and goes through `content`. This appendix does not change that — it adds the
byte-count check that `content` needs.

## Related

- Runbook 12 §14.2 — OneDrive as the export fallback; driveId and parentItemId for
  Documents > Daily Reports.
- Runbook 12 §14.3 — connected local folder as the preferred destination (absent on
  scheduled cloud firings, which is the normal case for this job).
- `simvay-brand-styling` — the white S-mark is the asset being shrunk; the brand rule
  (white mark on gradient only) is unaffected.
