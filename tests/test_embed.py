import numpy as np

from app.embed import load_or_create_embeddings




def test_load_or_create_embeddings_loads_existing_cache(tmp_path):
    cache_path = tmp_path / "embeddings.npy"

    expected = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        dtype=np.float32,
    )

    np.save(cache_path, expected)

    result = load_or_create_embeddings(
        texts=["tekst a", "tekst b"],
        cache_path=cache_path,
    )

    assert np.allclose(result, expected)