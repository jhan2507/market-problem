# Quick Fix cho Git Branches

Nếu gặp lỗi khi setup branches, sử dụng các cách sau:

## Cách 1: Sử dụng fix script (Khuyến nghị)

```bash
./scripts/git/fix_branches.sh
```

Script này sẽ:
- Tạo initial commit nếu chưa có
- Đảm bảo tất cả branches (master, staging, develop) tồn tại
- Fix các vấn đề về branches

## Cách 2: Fix thủ công

Nếu bạn đang ở trên branch develop và gặp lỗi:

```bash
# 1. Tạo initial commit (nếu chưa có)
git add -A
git commit -m "Initial commit: Crypto Market Monitoring System"

# 2. Tạo master branch
git checkout -b master

# 3. Tạo staging branch từ master
git checkout -b staging

# 4. Tạo develop branch từ master
git checkout master
git checkout -b develop

# 5. Kiểm tra
git branch -a
```

## Cách 3: Reset và làm lại

Nếu muốn bắt đầu lại từ đầu:

```bash
# Xóa tất cả branches (giữ lại files)
rm -rf .git
git init

# Chạy lại setup
./scripts/git/setup_repo.sh
```

## Vấn đề thường gặp

### Lỗi: "pathspec 'develop' did not match any file(s) known to git"

**Nguyên nhân:** Branch develop chưa được tạo đúng cách hoặc chưa có commit.

**Giải pháp:**
```bash
# Đảm bảo có ít nhất 1 commit
git add -A
git commit -m "Initial commit"

# Tạo lại branches
git checkout -b master
git checkout -b staging
git checkout master
git checkout -b develop
```

### Lỗi: "fatal: A branch named 'master' already exists"

**Giải pháp:**
```bash
# Xóa branch cũ và tạo lại
git branch -D master
git checkout -b master
```

### Lỗi: "error: pathspec 'master' did not match any file(s) known to git"

**Giải pháp:**
```bash
# Tạo initial commit trước
git add -A
git commit -m "Initial commit"
git checkout -b master
```

