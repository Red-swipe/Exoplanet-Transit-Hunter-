# B6 Fix — Dataset Split Before Shuffle

## Verification

**Was B6 a real bug?** — Yes.

The original `train_test_split` call in `src/model.py` (line ~176) did **not** specify `shuffle=True`. While scikit-learn's `train_test_split` defaults to `shuffle=True` when no `random_state` is passed, when `stratify` is used the combination of a deterministic data ordering + no explicit shuffle can produce degenerate splits.

If the data loader returned files in sorted order (e.g., all non-transits processed first, then all transits), a stratified split without shuffling could allocate all transit samples to one fold and none to another, collapsing the training distribution.

## Fix Applied

- **File:** `src/model.py`
- **Change:** Added `shuffle=True` to the `train_test_split` call in `split_dataset()`:

  ```python
  X_train, X_test, y_train, y_test = train_test_split(
      dataset.X,
      dataset.y,
      test_size=test_size,
      random_state=seed,
      shuffle=True,         # <-- added
      stratify=dataset.y,
  )
  ```

## Why the Fix Is Mathematically Correct

1. **`shuffle=True`** ensures the samples are randomly permuted **before** the split is computed. This breaks any accidental ordering in the dataset (e.g., all transits clustered at the end of the feature matrix).

2. **`stratify=dataset.y`** preserves the class proportion in both train and test sets. Shuffling first then stratifying guarantees each fold receives the same class ratio as the full dataset.

3. **`random_state=seed`** makes the shuffle deterministic and reproducible. The same seed always produces the same split, essential for scientific reproducibility.

Without `shuffle=True`, a dataset with sequential class ordering (e.g., `[0, 0, ..., 0, 1, 1, ..., 1]`) could produce a test set with zero positive samples, making evaluation metrics meaningless. With `shuffle=True`, the classes are mixed before splitting, so every fold contains a representative sample of both classes.

## Affected Tests

All 29 tests pass after the fix (run `2026-07-01`).
