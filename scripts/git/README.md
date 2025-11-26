# Git Management Scripts

Scripts quản lý Git repository và workflow.

## Setup

### Initial Setup
```bash
./scripts/git/setup_repo.sh [options]
```

**Options:**
- `--fix` - Fix branches nếu có vấn đề
- `--push` - Push branches sau khi setup

**Examples:**
```bash
# Setup cơ bản
./scripts/git/setup_repo.sh

# Setup và fix branches
./scripts/git/setup_repo.sh --fix

# Setup và push luôn
./scripts/git/setup_repo.sh --push
```

Script sẽ:
- Initialize Git repository (nếu chưa có)
- Add remote: `git@personal:jhan2507/market-problem.git`
- Tạo các branches: master, staging, develop
- Tạo initial commit nếu cần
- Tạo .gitattributes

## Branch Structure

```
master      → Production (live system)
staging     → Test/Staging environment  
develop     → Development (integration)
feature/*   → Feature branches
bugfix/*    → Bug fix branches
hotfix/*    → Hotfix for production
```

## Scripts

### setup_repo.sh
Setup Git repository và tạo các branches cơ bản.

```bash
./scripts/git/setup_repo.sh
```

### push.sh
Push branch lên remote với nhiều modes.

```bash
./scripts/git/push.sh [options] [branch] [remote]
```

**Options:**
- `--pull` - Pull từ remote trước khi push (safe, khuyến nghị)
- `--sync` - Sync với remote, xử lý conflicts tự động
- `--force` - Force push (nguy hiểm, ghi đè remote)
- Không có option - Push bình thường, check conflicts

**Examples:**
```bash
# Push bình thường (check conflicts)
./scripts/git/push.sh master

# Pull rồi push (safe)
./scripts/git/push.sh --pull master

# Sync với remote (xử lý conflicts)
./scripts/git/push.sh --sync master

# Force push (cẩn thận!)
./scripts/git/push.sh --force master
```

**Khuyến nghị:** Luôn dùng `--pull` nếu remote đã có code.

### create_branch.sh
Tạo branch mới.

```bash
./scripts/git/create_branch.sh <name> [base] [type]
```

Types:
- `feature` - New feature (default)
- `bugfix` - Bug fix
- `hotfix` - Hotfix for production
- `release` - Release preparation

Examples:
```bash
./scripts/git/create_branch.sh new-signal develop feature
./scripts/git/create_branch.sh fix-price master bugfix
./scripts/git/create_branch.sh critical-fix master hotfix
```

### merge_to_staging.sh
Merge branch vào staging.

```bash
./scripts/git/merge_to_staging.sh [source_branch]
```

Example:
```bash
./scripts/git/merge_to_staging.sh develop
```

### merge_to_production.sh
Merge staging vào production (master).

```bash
./scripts/git/merge_to_production.sh [source_branch]
```

**⚠️ WARNING:** Requires confirmation "DEPLOY"

**💡 Khuyến nghị:** Sử dụng `./scripts/release/golive.sh` thay vì script này để có đầy đủ workflow (version, build, deploy).

Example:
```bash
./scripts/git/merge_to_production.sh staging
```

### workflow.sh
Hiển thị Git workflow guide.

```bash
./scripts/git/workflow.sh
```

## Typical Workflow

### Feature Development

1. **Create feature branch:**
   ```bash
   ./scripts/git/create_branch.sh my-feature develop feature
   ```

2. **Develop and commit:**
   ```bash
   git add .
   git commit -m "Add new feature"
   ```

3. **Push feature branch:**
   ```bash
   ./scripts/git/push.sh feature/my-feature
   ```

4. **Merge to develop:**
   ```bash
   git checkout develop
   git merge feature/my-feature
   git push origin develop
   ```

5. **Merge to staging (for testing):**
   ```bash
   ./scripts/git/merge_to_staging.sh develop
   ```

6. **Test on staging, then merge to production:**
   ```bash
   ./scripts/git/merge_to_production.sh staging
   ```

7. **Deploy to production:**
   ```bash
   ./scripts/release/deploy.sh production
   ```

### Hotfix Workflow

1. **Create hotfix from master:**
   ```bash
   ./scripts/git/create_branch.sh critical-fix master hotfix
   ```

2. **Fix and commit:**
   ```bash
   # Make fixes
   git commit -m "Fix critical issue"
   ```

3. **Merge to master:**
   ```bash
   ./scripts/git/merge_to_production.sh hotfix/critical-fix
   ```

4. **Also merge to staging:**
   ```bash
   ./scripts/git/merge_to_staging.sh hotfix/critical-fix
   ```

5. **Deploy:**
   ```bash
   ./scripts/release/deploy.sh production
   ```

## Best Practices

1. **Always work on feature branches**, never directly on master/staging
2. **Test on staging** before merging to production
3. **Use descriptive commit messages**
4. **Pull before push** to avoid conflicts
5. **Tag releases** on master branch
6. **Keep branches up to date** with base branch

## Git Hooks (Optional)

Có thể tạo git hooks để tự động:
- Validate code before commit
- Run tests before push
- Update version on merge to master

Example `.git/hooks/pre-push`:
```bash
#!/bin/bash
# Run tests before push
./scripts/utils/validate_config.sh
```

## Troubleshooting

### Merge conflicts
```bash
# Resolve conflicts manually
git status
# Edit conflicted files
git add .
git commit -m "Resolve merge conflicts"
```

### Undo last commit (keep changes)
```bash
git reset --soft HEAD~1
```

### Undo last commit (discard changes)
```bash
git reset --hard HEAD~1
```

### Force push (use with caution)
```bash
git push --force origin branch-name
```

