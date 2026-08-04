# 📂 OOP 저장소 개별 폴더 업로드 & 충돌 해결 가이드

상위 저장소(`Dev_hsj`)의 `.gitignore` 규칙을 유지하면서, 특정 날짜 폴더만 GitHub `OOP` 저장소에 **폴더 구조 그대로(`OOP/0804/...`)** 안전하게 올리는 표준 방법 및 대처법 가이드입니다.

---

## 🛠️ 최초 1회 실행 (원격 저장소 등록)

VS Code 터미널(`Dev_hsj` 경로)에서 최초 1회만 실행합니다.

    git remote add oop-repo https://github.com/inpusanstation-code/OOP.git

---

## 🚀 기본 업로드 절차 (3단계)

`0804` 대신 올리고 싶은 폴더명(예: `0805`, `0811` 등)으로 이름만 바꾸어 실행하세요.
로컬 파일 수정 후 재업로드할 때도 똑같이 아래 3단계를 수행하면 됩니다.

    # 1. 대상 폴더에 경로 명찰을 붙인 임시 커밋 패키지 생성 (.gitignore 자동 적용)
    git subtree split --prefix=0804 --annotate=0804/ -b branch-0804

    # 2. OOP 저장소의 main 브랜치로 푸시
    git push oop-repo branch-0804:main

    # 3. 작업에 사용한 임시 로컬 브랜치 삭제 (정리)
    git branch -D branch-0804

---

## ⚠️ 꼬이는 상황(충돌) 및 해결 대처법

### 1. 내 컴퓨터(`Dev_hsj`)의 `git pull`이나 `Sync`가 꼬일 확률
* **결론:** **0% (꼬이지 않음)**
* **이유:** 작업을 임시 브랜치에서 처리하고 즉시 삭제하므로, 내 컴퓨터의 메인 저장소(`Dev_hsj`) 히스토리에는 아무런 영향을 주지 않습니다. 평소대로 Sync/Push 하시면 됩니다.

### 2. 푸시 중 `non-fast-forward` (충돌) 에러가 발생하는 원인
* **원인:** GitHub 웹사이트에서 `OOP` 저장소 내의 파일(예: README.md)을 직접 수정했거나 삭제한 경우, 내 로컬 내역과 GitHub의 내역이 서로 달라져 발생합니다.

### 💡 충돌 발생 시 해결법 (강제 덮어쓰기)
`OOP` 저장소는 내 로컬 파일(`Dev_hsj`)의 결과물을 제출/백업하는 용도이므로, 충돌 발생 시 2번 푸시 명령에 `--force` 옵션을 붙여 내 로컬 상태로 덮어씌우면 깔끔하게 해결됩니다.

    # 1. 임시 패키지 생성
    git subtree split --prefix=0804 --annotate=0804/ -b branch-0804

    # 2. --force 옵션을 붙여 강제 푸시 (충돌 해결)
    git push oop-repo branch-0804:main --force

    # 3. 임시 브랜치 삭제
    git branch -D branch-0804

---

## ✨ 핵심 요약
1. **`.gitignore` 완벽 적용:** `Dev_hsj` 상위의 `.gitignore`가 적용되어 `.vs`, `.venv` 등 캐시 파일이 자동 제거됩니다.
2. **원하는 폴더 구조 유지:** GitHub `OOP` 저장소에 `OOP/0804/...` 형태로 깔끔하게 저장됩니다.
3. **가장 중요한 원칙:** 파일 수정은 항상 **내 로컬 컴퓨터(`Dev_hsj`)에서만** 진행하고 `OOP` 저장소로 올려주는 흐름을 유지하세요.