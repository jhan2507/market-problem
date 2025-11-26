# Git Scripts Index

Danh sách tất cả scripts và cách sử dụng.

## Core Scripts (5 scripts)

### 1. setup_repo.sh
**Setup repository và branches**

```bash
./scripts/git/setup_repo.sh [--fix] [--push]
```

- `--fix` - Fix branches nếu có vấn đề
- `--push` - Push branches sau khi setup

### 2. push.sh
**Push với nhiều modes**

```bash
./scripts/git/push.sh [--pull|--sync|--force] [branch] [remote]
```

- `--pull` - Pull rồi push (safe)
- `--sync` - Sync với remote (xử lý conflicts)
- `--force` - Force push (dangerous)
- Không có option - Push bình thường

### 3. create_branch.sh
**Tạo branch mới**

```bash
./scripts/git/create_branch.sh <name> [base] [type]
```

Types: feature, bugfix, hotfix, release

### 4. merge_to_staging.sh
**Merge vào staging**

```bash
./scripts/git/merge_to_staging.sh [source_branch]
```

### 5. merge_to_production.sh
**Merge vào production (master)**

```bash
./scripts/git/merge_to_production.sh [source_branch]
```

## Helper Scripts (2 scripts)

### 6. initial_push.sh
**Push lần đầu (wrapper)**

```bash
./scripts/git/initial_push.sh
```

Tương đương: `setup_repo.sh --push`

### 7. workflow.sh
**Hiển thị workflow guide**

```bash
./scripts/git/workflow.sh
```

## Quick Reference

### Setup mới
```bash
./scripts/git/setup_repo.sh --push
```

### Push an toàn
```bash
./scripts/git/push.sh --pull [branch]
```

### Fix branches
```bash
./scripts/git/setup_repo.sh --fix
```

### Tạo feature branch
```bash
./scripts/git/create_branch.sh my-feature develop feature
```

### Merge to staging
```bash
./scripts/git/merge_to_staging.sh develop
```

### Merge to production
```bash
./scripts/git/merge_to_production.sh staging
```

## Scripts đã được merge

Các scripts sau đã được merge vào scripts chính:

- ❌ `pull_and_push.sh` → merged vào `push.sh --pull`
- ❌ `sync_with_remote.sh` → merged vào `push.sh --sync`
- ❌ `fix_branches.sh` → merged vào `setup_repo.sh --fix`

## Tổng số scripts: 7 (giảm từ 10+)

