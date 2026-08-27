공통 변수 공유제시해주신 캐릭터, 몬스터, 스킬, 전투 기믹(열, 스턴, 행동 순서, 전역 상태 등)을 기반으로 팀 프로젝트 분업 시 공통으로 사용할 핵심 주요 변수 명세서입니다.

팀원 간 데이터 형태(타입)가 다르면 코드 통합 때 충돌이 발생하므로, 아래와 같이 변수명과 데이터 구조를 표준화하여 공유하는 것을 추천합니다.



1. 전역 게임 상태 관리 변수 (Game State)

게임의 전체 라이프사이클과 던전 노드, 턴 흐름을 제어하는 변수입니다.

| 변수명 | 데이터 타입 | 설명 및 예시 |
| --- | --- | --- |
| current_node | Integer | 현재 진행 중인 맵 노드 번호 (예: 1 ~ 12)

 |
| game_state | String | 현재 게임 화면 상태 ("MAP", "BATTLE", "SHOP", "GAME_OVER")

 |
| turn_count | Integer | 현재 전투의 라унд/턴 수 |
| turn_order | List[Object] | 캐릭터와 몬스터의 spd 기반 행동 순서 리스트 |



2. 엔티티 데이터 모델 변수 (Character & Enemy Common)

아군 파티(전사, 마법사, 지원가)와 적(고블린, 오크 등)이 공통으로 사용하는 속성 변수입니다.

| 변수명 | 데이터 타입 | 설명 및 예시 |
| --- | --- | --- |
| id / name | String | 엔티티 식별자 및 이름 (예: "Warrior", "전사", "고블린")

 |
| hp / max_hp | Integer | 현재 체력 및 최대 체력 (예: 전사 180, 드래곤 800)

 |
| spd | Integer | 기본 속도 수치 (예: 늑대 16, 마법사 15, 골렘 5)

 |
| position | Integer | 현재 위치/열 (1 ~ 4열)

 |
| is_stunned | Boolean | 스턴 여부 (True/False). True일 경우 턴 시작 시 해제되며 턴 소모 |
| buffs / debuffs | List[Dict] | 지속 효과 배열. 예: [{"type": "atk_up", "value": 0.2, "duration": 2}]<br> |
| status_effects | List[Dict] | 출혈/중독 등 상태이상. 예: [{"type": "bleed", "damage": 5, "duration": 2}]<br> |
| soul_bound_target | Object | (부두술사 전용) 영혼 결속으로 데미지의 50%를 대신 맞을 대상 |



3. 스킬 및 행동 데이터 변수 (Skill System)

스킬의 범위, 타깃 위치, 스턴/부과 효과 등을 관리하는 변수입니다.


변수명
	데이터 타입
	설명 및 예시

skill_id
	String
	스킬 식별 키 (예: "fireball", "bone_cleave")

target_positions
	List[Integer]
	스킬 사용 가능/타격 열 범주 (예: 파이어볼 [2, 3, 4], 뼈가르기 [1, 2])

is_aoe
	Boolean
	광역 공격 여부 (True/False)

min_dmg / max_dmg
	Integer
	데미지 범위 (예: 신의 심판 15 ~ 25, 파이어볼 20 ~ 40)

accuracy
	Float
	명중률 (예: 아마겟돈 0.10, 회전 격멸 0.70, 기본 1.0)

stun_chance
	Float
	스턴 부여 확률 (예: 체인라이트닝 0.65, 몽둥이 0.20, 포효 0.40)

position_shift
	Integer
	위치 이동 값 (예: 뼈가르기 밀쳐내기 +1, 가시덩굴 당기기 -1)





4. 전투 연산 및 UI 표시 변수 (Battle System)

요청하신 '매 라운드 전체 공격 표시' 및 계산용 변수입니다.

| 변수명 | 데이터 타입 | 설명 및 예시 |
| --- | --- | --- |
| next_actions | Dict | 적들이 다음 턴에 실행할 미리 결정된 행동 구조체 <br>

<br>예: {"오크": "몽둥이 내리치기", "늑대": "목덜미 물어뜯기"} |
| action_queue | List[Dict] | spd에 의해 정렬된 이번 라운드의 전체 순서 배열

 |
| battle_logs | List[String] | 텍스트 UI에 출력할 전투 메시지 리스트 |



💡 팀 프로젝트 분업 가이드 (추천 역할 분담)

1. 팀원 A (데이터 & 엔티티 담당):

* 캐릭터/몬스터 클래스 정의 (hp, spd, position 등)
* 버프/데뷔프/스턴 수명(duration) 감소 로직 처리

1. 팀원 B (스킬 & 전투 계산 엔진 담당):

* 명중률(accuracy), 데미지 딜링, 위치 이동(position_shift) 계산
* 스턴 판정 및 턴 넘기기, 출혈/영혼 결속 데미지 처리

1. 팀원 C (턴 순서 & 적 AI/행동 예측 담당):

* spd 기반 action_queue 정렬 및 스피드 버프 반영 (시간왜곡, 지진파)
* 몬스터 패턴 선정 및 next_actions (다음 공격 예고) 시스템 구현

1. 팀원 D (UI & 메인 라이프사이클 담당):

* while 루프 기반 전역 상태 관리 (MAP $\rightarrow$ BATTLE 등)
* 라운드 시작 시 적 전체의 예정된 공격 정보(next_actions) 출력 화면 구성

