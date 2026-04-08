from config.settings import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_file(file: dict) -> list:
    """Split a file into overlapping line-based chunks with metadata."""
    lines = file["content"].splitlines()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP

    for start in range(0, len(lines), step):
        end = min(start + CHUNK_SIZE, len(lines))
        chunk_text = "\n".join(lines[start:end])
        if chunk_text.strip():
            chunks.append({
                "id": f"{file['path']}::{start}-{end}",
                "text": chunk_text,
                "metadata": {
                    "path": file["path"],
                    "language": file["language"],
                    "start_line": start + 1,
                    "end_line": end
                }
            })
        if end == len(lines):
            break

    return chunks


def chunk_all_files(files: list) -> list:
    all_chunks = []
    for f in files:
        all_chunks.extend(chunk_file(f))
    print(f"[chunker] {len(all_chunks)} chunks from {len(files)} files")
    return all_chunks
