"""
========================================================================
 턴제 RPG 전투 시스템 (Turn-Based RPG Battle System)
========================================================================
 이 코드는 파이썬으로 만든 '턴제 전투' 게임 시스템입니다.
 마치 포켓몬이나 여러 모바일 RPG 게임처럼, 아군 파티와 적 파티가
 서로 번갈아가며(속도 순서대로) 스킬을 사용해 싸우는 구조입니다.

 [전체 구조를 미리 이해하고 읽으면 좋습니다]
 1) Skill 클래스        : 스킬(공격/힐/버프 등) 하나하나의 '설계도'
 2) Entity 클래스        : 전사, 마법사, 몬스터 등 '캐릭터' 하나하나의 '설계도'
 3) BattleManager 클래스 : 전투 전체를 진행시키는 '진행자(사회자)' 역할
 4) create_hero_party() / create_enemy_encounter() : 실제 캐릭터들을 만들어내는 함수
 5) if __name__ == "__main__": 부분 : 프로그램이 실제로 시작되는 지점

 프로그래밍에서 이렇게 "설계도(클래스)"와 "실제 데이터(객체)"를 나누어
 만드는 방식을 객체지향 프로그래밍(OOP)이라고 부릅니다.
========================================================================
"""

# 전투 시스템 (공통 변수 적용)
import random  # 주사위를 굴리듯 무작위 확률을 계산할 때 사용 (예: 명중률, 데미지 범위)
from typing import List, Dict, Optional, Any
# List, Dict, Optional, Any 는 '이 변수에 어떤 종류의 데이터가 들어가는지'를
# 사람이 읽기 쉽게 표시해주는 타입 힌트(type hint)입니다.
# 예) List[int] = 정수들이 여러 개 들어있는 리스트
#     Dict[str, int] = 문자열 키와 정수 값으로 이루어진 딕셔너리
#     Optional[Entity] = Entity 이거나, 혹은 값이 없을 수도 있음(None)
#     Any = 어떤 타입이든 가능 (제한 없음)
# 이 힌트들은 프로그램 실행에는 영향을 주지 않고, 오직 '가독성'을 위한 것입니다.


# ==========================================
# 3. 스킬 및 행동 데이터 모델 (Skill System)
# ==========================================
class Skill:
    """
    스킬(기술) 하나를 표현하는 클래스입니다.
    예를 들어 "파이어볼", "회전 격멸" 같은 스킬 각각이 이 클래스로 만들어진
    하나의 '객체(instance)'가 됩니다.

    이 클래스 자체는 '행동을 실행하지 않습니다'. 즉, 스킬이 어떤 효과를
    가지고 있는지에 대한 '데이터(정보)'만 저장하는 역할을 합니다.
    실제로 스킬을 사용해서 데미지를 주고 효과를 적용하는 로직은
    뒤에 나오는 BattleManager.execute_skill() 함수가 담당합니다.
    """
    def __init__(
        self,
        skill_id: str,              # 스킬을 구분하기 위한 고유 이름표 (예: "fireball")
        name: str,                  # 화면에 보여줄 스킬 이름 (예: "파이어볼")
        target_positions: List[int],# 이 스킬이 공격/영향을 줄 수 있는 '열(줄)' 번호들
                                     # 예) [1, 2] 라면 상대편 1열과 2열만 공격 가능
        is_aoe: bool = False,       # AOE = Area Of Effect(광역 효과). True면 여러 명을 동시에 공격
        min_dmg: int = 0,           # 최소 피해량 (혹은 회복량의 최소값)
        max_dmg: int = 0,           # 최대 피해량 (혹은 회복량의 최대값)
        accuracy: float = 1.0,      # 명중률. 1.0 = 100% 명중, 0.5 = 50% 확률로 빗나감
        stun_chance: float = 0.0,   # 상대를 기절시킬 확률 (0.0 ~ 1.0)
        position_shift: int = 0,    # 공격 후 대상의 위치(열)를 바꾸는 효과
                                     # +1: 밀쳐내기(뒤로 한 칸 이동), -1: 당기기(맨 앞으로 끌어옴)
        target_type: str = "enemy", # 이 스킬이 누구를 대상으로 하는지 구분하는 값
                                     # "enemy": 상대방 공격
                                     # "ally": 아군 대상
                                     # "self": 자기 자신에게만 적용
                                     # "all_allies": 아군 전체에게 적용
                                     # (아래 execute_skill에서 더 세부적으로
                                     #  "self_buff", "ally_heal" 등도 사용됩니다)
        effect: Optional[Dict[str, Any]] = None,
                                     # 스킬의 부가 효과를 담는 딕셔너리
                                     # 예) {"type": "bleed", "damage": 5, "duration": 2}
                                     #     -> "5의 피해를 주는 출혈을 2턴 동안 건다"
        description: str = ""       # 플레이어에게 보여줄 스킬 설명 문구
    ):
        # 아래는 위에서 전달받은 매개변수들을
        # 이 스킬 객체 자신(self)의 속성(변수)으로 그대로 저장하는 부분입니다.
        # 즉 "이 스킬의 이름은 무엇이고, 데미지는 얼마고..." 를 기억해두는 것입니다.
        self.skill_id = skill_id
        self.name = name
        self.target_positions = target_positions
        self.is_aoe = is_aoe
        self.min_dmg = min_dmg
        self.max_dmg = max_dmg
        self.accuracy = accuracy
        self.stun_chance = stun_chance
        self.position_shift = position_shift
        self.target_type = target_type
        # effect가 None으로 넘어왔다면(아무 효과도 지정 안 했다면) 빈 딕셔너리 {}로 채워서
        # 나중에 skill.effect.get(...) 을 호출해도 에러가 나지 않게 안전장치를 둔 것입니다.
        self.effect = effect or {}
        self.description = description


# ==========================================
# 2. 엔티티 데이터 모델 (Entity Model)
# ==========================================
class Entity:
    """
    전투에 참여하는 '캐릭터' 한 명(혹은 한 마리)을 표현하는 클래스입니다.
    전사, 마법사, 지원가 같은 아군뿐 아니라 오크, 드래곤 같은 적도
    모두 이 Entity 클래스를 이용해서 만들어집니다.

    이 클래스는 캐릭터의 '상태'(체력, 위치, 버프 등)를 저장하고,
    상태를 변경하는 몇 가지 동작(메서드)들을 가지고 있습니다.
    """
    def __init__(self, id_str: str, name: str, max_hp: int, spd: int, team: str, is_boss: bool = False):
        self.id: str = id_str            # 캐릭터를 구분하는 고유 ID (예: "warrior", "orc_1")
        self.name: str = name            # 화면에 표시될 이름 (예: "전사", "오크")
        self.max_hp: int = max_hp        # 최대 체력
        self.hp: int = max_hp            # 현재 체력 (처음엔 최대 체력과 동일하게 시작)
        self.spd: int = spd              # 기본 속도(SPD). 속도가 높을수록 먼저 행동함
        self.team: str = team            # 소속 팀. "player"(아군) 또는 "enemy"(적군)
        self.is_boss: bool = is_boss     # 보스 몬스터인지 여부 (지금 코드에서는 표시용으로만 사용)
        self.position: int = 1           # 현재 서 있는 위치(열). 1~4열 (숫자가 작을수록 앞줄)

        self.is_stunned: bool = False    # 기절 상태인지 여부. True면 이번 턴에 행동 못 함
        self.buffs: List[Dict[str, Any]] = []
        # 나에게 걸린 '좋은 효과' 목록. 예: [{"type": "atk_up", "value": 0.2, "duration": 2}]
        # -> "공격력이 20% 증가하는 효과가 2턴 동안 지속된다"는 의미
        self.debuffs: List[Dict[str, Any]] = []
        # 나에게 걸린 '나쁜 효과' 목록. 예: [{"type": "def_down", "value": 0.25, "duration": 2}]
        # -> "방어력이 25% 감소하는 효과가 2턴 동안 지속된다"는 의미
        self.status_effects: List[Dict[str, Any]] = []
        # 지속 피해 같은 상태이상 목록. 예: [{"type": "bleed", "damage": 5, "duration": 2}]
        # -> "매 턴 시작마다 5의 피해를 입는 출혈이 2턴 동안 지속된다"는 의미
        self.soul_bound_target: Optional['Entity'] = None
        # 부두술사 전용 특수 상태: "내가 받는 피해의 절반을 대신 받아줄 대상"
        # Optional['Entity'] 는 "Entity 타입이거나 아직 아무도 지정 안 된(None) 상태"라는 뜻입니다.

        self.skills: List[Skill] = []    # 이 캐릭터가 사용할 수 있는 스킬 목록

    def is_alive(self) -> bool:
        """살아있는지(HP가 0보다 큰지) 확인하는 함수. True/False를 반환합니다."""
        return self.hp > 0

    def get_effective_spd(self) -> int:
        """
        '실제로 적용되는' 속도를 계산합니다.
        기본 속도(self.spd)에 버프로 증가한 속도, 디버프로 감소한 속도를 반영합니다.
        이렇게 별도 함수로 계산하는 이유는, 매번 버프/디버프를 직접
        더하고 빼는 대신 '현재 속도가 얼마인지' 한 번에 물어볼 수 있게 하기 위함입니다.
        """
        spd_val = self.spd
        for b in self.buffs:                       # 나에게 걸린 버프들을 하나씩 확인
            if b.get("type") == "spd_up":           # 그중 "속도 증가" 버프가 있다면
                spd_val += int(b.get("value", 0))   # 그 수치만큼 더해줌
        for d in self.debuffs:                      # 나에게 걸린 디버프들을 하나씩 확인
            if d.get("type") == "spd_down":         # 그중 "속도 감소" 디버프가 있다면
                spd_val -= int(d.get("value", 0))   # 그 수치만큼 빼줌
        return max(1, spd_val)  # 속도가 0 이하로 내려가지 않도록 최소값 1을 보장

    def get_atk_multiplier(self) -> float:
        """
        공격력 배율을 계산합니다. 기본값은 1.0(=100%, 즉 배율 없음)이고,
        "공격력 증가" 버프가 있으면 그 값만큼 배율을 더 높여줍니다.
        예) 20% 증가 버프가 있으면 최종 배율은 1.2가 되어, 데미지 계산 시 1.2배가 곱해집니다.
        """
        mult = 1.0
        for b in self.buffs:
            if b.get("type") == "atk_up":
                mult += float(b.get("value", 0.0))
        return mult

    def get_accuracy_modifier(self) -> float:
        """
        내가 가진 '명중률 감소' 디버프의 총합을 계산합니다.
        이 값은 나중에 상대방이 나를 공격할 때 '명중률에서 얼마를 깎을지'로 사용됩니다.
        (즉, 이 함수는 "내가 얼마나 맞추기 어려운 상태인지"를 나타냅니다.)
        """
        mod = 0.0
        for d in self.debuffs:
            if d.get("type") == "acc_down":
                mod += float(d.get("value", 0.0))
        return mod

    def take_damage(self, raw_dmg: int, team_entities: List['Entity'], logs: List[str]) -> int:
        """
        이 캐릭터가 피해를 입는 함수입니다.
        raw_dmg      : 아직 방어력 등이 적용되지 않은 '원래' 피해량
        team_entities: 이 캐릭터와 같은 팀의 캐릭터 목록 (영혼 결속 확인용)
        logs         : 전투 로그(전투 중 일어난 일을 기록하는 문자열 리스트)
        반환값       : 실제로 적용된(감소 처리까지 끝난) 최종 피해량
        """
        if not self.is_alive():
            # 이미 죽은 대상이면 피해를 줄 필요가 없으므로 0을 반환하고 함수 종료
            return 0

        # ---- 방어력 계산 ----
        def_mod = 1.0  # 1.0 = 원래 피해량 그대로 받는다는 뜻 (방어 보정 배율)
        for b in self.buffs:
            if b.get("type") == "def_up":
                # 방어력 증가 버프가 있으면 배율을 낮춰서(=피해를 덜 받게) 만듦
                def_mod -= float(b.get("value", 0.0))
        for d in self.debuffs:
            if d.get("type") == "def_down":
                # 방어력 감소 디버프가 있으면 배율을 높여서(=피해를 더 받게) 만듦
                def_mod += float(d.get("value", 0.0))

        # 최종 피해 = 원래 피해 * 방어 보정 배율
        # max(0.1, def_mod) 는 방어 보정 배율이 지나치게 낮아져도
        # 최소한 원래 피해의 10%는 반드시 받도록 하는 안전장치입니다.
        final_dmg = int(raw_dmg * max(0.1, def_mod))

        # ---- 부두술사의 '영혼 결속' 효과 판정 ----
        # 만약 내가 누군가와 영혼이 묶여 있고, 그 대상이 살아있으며, 같은 팀이라면
        if self.soul_bound_target and self.soul_bound_target.is_alive() and (self.soul_bound_target in team_entities):
            transfer_dmg = int(final_dmg * 0.5)              # 피해의 절반을 계산
            final_dmg -= transfer_dmg                        # 나는 그만큼 피해가 줄어들고
            self.soul_bound_target.hp = max(0, self.soul_bound_target.hp - transfer_dmg)
            # 대신 그 절반을 묶여있는 대상이 입도록 처리 (체력이 음수가 되지 않게 max(0, ...) 사용)
            logs.append(f"  🔗 [영혼 결속] {self.soul_bound_target.name}이(가) {transfer_dmg}의 피해를 대신 흡수했습니다!")

        # 최종적으로 내 체력에서 final_dmg만큼 깎되, 0 밑으로는 내려가지 않게 처리
        self.hp = max(0, self.hp - final_dmg)
        return final_dmg  # 실제로 적용된 피해량을 돌려줌 (로그 출력 등에 사용)

    def heal(self, amount: int) -> int:
        """
        체력을 회복하는 함수입니다.
        amount: 회복하려는 수치
        반환값: 실제로 회복된 수치 (최대 체력을 넘어서까지는 회복되지 않으므로,
                요청한 amount보다 적게 회복될 수도 있습니다)
        """
        if not self.is_alive():
            return 0  # 죽은 캐릭터는 회복이 불가능
        # 실제 회복량은 "회복하려는 양"과 "최대 체력까지 남은 여유분" 중 더 작은 값
        actual = min(self.max_hp - self.hp, amount)
        self.hp += actual
        return actual

    def process_start_of_turn(self, logs: List[str]) -> bool:
        """
        이 캐릭터의 턴이 시작될 때 호출되는 함수입니다.
        출혈 같은 지속 피해를 먼저 처리하고, 기절 상태인지 확인합니다.
        반환값: True이면 "이번 턴에 실제로 행동할 수 있다", False이면 "행동 불가"
        """
        # 1. 상태이상(출혈 등) 처리
        rem_status = []  # 이번 턴 처리 후에도 '남아있어야 할' 상태이상들을 담을 새 리스트
        for s in self.status_effects:
            if s.get("type") == "bleed":
                dmg = s.get("damage", 0)
                self.hp = max(0, self.hp - dmg)  # 출혈 피해를 입힘 (0 밑으로 내려가지 않게)
                logs.append(f"🩸 {self.name}이(가) 출혈로 {dmg}의 피해를 입었습니다! (HP: {self.hp}/{self.max_hp})")
                s["duration"] -= 1                # 지속 턴을 1 감소
                if s["duration"] > 0:
                    rem_status.append(s)          # 아직 지속 턴이 남아있다면 유지 목록에 추가
                # duration이 0 이하가 되면 rem_status에 넣지 않으므로 자동으로 사라짐
        self.status_effects = rem_status  # 처리 결과로 상태이상 목록을 갱신

        # 2. 스턴(기절) 체크
        if self.is_stunned:
            self.is_stunned = False  # 기절은 한 턴만 지속되므로 여기서 즉시 해제
            logs.append(f"💫 {self.name}은(는) 기절에서 깨어났지만 턴을 소모합니다!")
            return False  # 이번 턴은 행동 불가
        return self.is_alive()  # 기절도 아니고 살아있다면 행동 가능(True)

    def tick_effects(self):
        """
        라운드가 끝날 때 호출되어, 버프와 디버프의 남은 지속 턴을 1씩 줄이고
        지속 턴이 0이 된 효과는 목록에서 제거합니다.
        """
        # 리스트 컴프리헨션(list comprehension): 반복문 + 조건문을 한 줄로 표현하는 문법
        # "self.buffs 안의 각 항목 b에 대해 self._decrement(b)를 실행했을 때
        #  True를 반환한 것들만 모아서 새 리스트로 만든다"는 의미입니다.
        self.buffs = [b for b in self.buffs if self._decrement(b)]
        self.debuffs = [d for d in self.debuffs if self._decrement(d)]

    @staticmethod
    def _decrement(effect_dict: Dict[str, Any]) -> bool:
        """
        @staticmethod: 이 함수는 특정 캐릭터(self)의 정보를 사용하지 않고,
        전달받은 effect_dict(효과 하나)만 가지고 동작하는 '독립적인 도구 함수'라는 뜻입니다.
        효과의 지속 턴(duration)을 1 줄이고, 아직 턴이 남아있으면(0보다 크면) True를 반환합니다.
        위 tick_effects()에서 "살려둘지 말지"를 판단하는 데 사용됩니다.
        """
        effect_dict["duration"] -= 1
        return effect_dict["duration"] > 0


# ==========================================
# 1 & 4. 전투 시스템 및 게임 매니저 (Battle System)
# ==========================================
class BattleManager:
    """
    전투 전체의 흐름을 관리하는 '진행자' 클래스입니다.
    아군 목록과 적군 목록을 받아서, 라운드를 진행하고,
    누가 언제 행동할지 정하고, 화면에 상황을 출력하는 등
    전투와 관련된 모든 '운영'을 담당합니다.
    """
    def __init__(self, heroes: List[Entity], enemies: List[Entity]):
        # ---- 1. 전역 상태 관리 변수 ----
        self.current_node: int = 1     # 현재 진행 중인 던전의 몇 번째 방(전투)인지 (확장용 변수)
        self.game_state: str = "BATTLE" # 현재 게임 상태 ("BATTLE" 진행 중, "GAME_OVER" 종료 등)
        self.turn_count: int = 1        # 현재 몇 번째 라운드(턴)인지
        self.turn_order: List[Entity] = []  # 이번 라운드에 행동할 순서대로 정렬된 캐릭터 목록

        # ---- 4. 전투 연산 및 UI 표시 변수 ----
        self.next_actions: Dict[str, Dict[str, Any]] = {}
        # 적들이 '다음에 어떤 스킬을 쓸지' 미리 정해두고 플레이어에게 예고하기 위한 딕셔너리
        # 예) {"orc_1": {"unit_name": "오크", "skill": <Skill객체>, ...}}
        self.action_queue: List[Dict[str, Any]] = []
        # 이번 라운드에 실제로 행동을 처리할 순서 목록 (turn_order를 기반으로 생성)
        self.battle_logs: List[str] = []
        # 전투 중 발생한 이벤트(공격, 회복, 상태이상 등)를 문자열로 기록해두는 리스트
        # 나중에 print()로 화면에 한꺼번에 출력하기 위해 사용됩니다.

        self.heroes: List[Entity] = heroes    # 아군 파티 목록
        self.enemies: List[Entity] = enemies  # 적군 파티 목록
        self._update_positions()  # 초기 위치(몇 열에 서 있는지)를 세팅

    def _update_positions(self):
        """
        배열(리스트) 순서에 따라 각 캐릭터의 position(1~4열)을 다시 계산합니다.
        예) heroes 리스트의 0번째 캐릭터는 1열, 1번째 캐릭터는 2열, ...
        함수 이름 앞의 밑줄(_)은 "이 함수는 클래스 내부에서만 사용하는
        보조 함수입니다"라는 파이썬의 관례적인 표시입니다.
        """
        for i, h in enumerate(self.heroes):
            # enumerate()는 리스트를 순회하면서 "인덱스(순번)"와 "값"을 동시에 꺼내줍니다.
            h.position = i + 1  # 인덱스는 0부터 시작하므로 열 번호는 +1 해줌
        for i, e in enumerate(self.enemies):
            e.position = i + 1

    def clean_dead(self):
        """
        전투 중간중간 호출되어, 죽은 캐릭터를 로그에 기록하고
        heroes/enemies 리스트에서 완전히 제거합니다.
        """
        for h in self.heroes:
            if not h.is_alive():
                self.battle_logs.append(f"💀 아군 [{h.name}]이(가) 쓰러졌습니다!")
        for e in self.enemies:
            if not e.is_alive():
                self.battle_logs.append(f"💥 적 [{e.name}]을(를) 처치했습니다!")

        # 살아있는 캐릭터만 남기고 리스트를 새로 만듦 (죽은 캐릭터는 자동으로 제거됨)
        self.heroes = [h for h in self.heroes if h.is_alive()]
        self.enemies = [e for e in self.enemies if e.is_alive()]
        self._update_positions()  # 누군가 죽어서 대열이 바뀌었으므로 위치를 다시 정리

    def shift_entity_position(self, team_list: List[Entity], target_entity: Entity, shift: int):
        """
        position_shift 효과를 실제로 적용하는 함수입니다.
        team_list     : 위치를 바꿀 대상이 속한 팀의 리스트 (heroes 또는 enemies)
        target_entity : 위치를 바꿀 캐릭터
        shift         : +1이면 밀쳐내기(뒤로 한 칸), -1이면 당기기(맨 앞으로)
        """
        if target_entity not in team_list:
            return  # 혹시 리스트에 없는 대상이면 아무것도 하지 않고 종료 (안전장치)

        cur_idx = team_list.index(target_entity)  # 현재 리스트에서 이 캐릭터의 위치(인덱스)를 찾음

        if shift > 0 and cur_idx + 1 < len(team_list):
            # 밀쳐내기: 바로 뒤 칸의 캐릭터와 자리를 맞바꿈 (뒤에 자리가 있을 때만 가능)
            team_list[cur_idx], team_list[cur_idx + 1] = team_list[cur_idx + 1], team_list[cur_idx]
            self.battle_logs.append(f"  ↪️ [밀쳐내기] {target_entity.name}이(가) 뒤로 밀려났습니다!")
        elif shift < 0 and cur_idx > 0:
            # 당기기: 리스트에서 빼낸 뒤(pop), 맨 앞(0번 인덱스)에 다시 끼워 넣음(insert)
            team_list.pop(cur_idx)
            team_list.insert(0, target_entity)
            self.battle_logs.append(f"  ↩️ [당기기] {target_entity.name}이(가) 1열로 끌려왔습니다!")

        self._update_positions()  # 순서가 바뀌었으므로 position 값을 다시 계산

    def plan_enemy_actions(self):
        """
        매 라운드가 시작될 때, 모든 살아있는 적이 '이번에 어떤 스킬을 쓸지'
        미리 정해두는 함수입니다. (플레이어에게 예고 UI로 보여주기 위함이며,
        일부 간단한 '패턴형 AI'도 여기에 포함되어 있습니다.)
        """
        self.next_actions.clear()  # 이전 라운드의 예고 정보를 초기화
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue  # 죽은 적은 행동을 계획할 필요 없음

            # ---- 스킬 선택 로직 (간단한 규칙 기반 AI) ----
            chosen_skill = None
            if enemy.name == "오크" and enemy.hp <= enemy.max_hp * 0.5 and not any(b.get("type") == "atk_up" for b in enemy.buffs):
                # 오크는 체력이 50% 이하이고, 아직 공격력 증가 버프가 없다면
                # "분노의 함성(furious_roar)" 스킬을 최우선으로 사용하도록 함
                # any(...)는 "조건을 만족하는 항목이 하나라도 있으면 True"를 반환하는 함수
                chosen_skill = next((s for s in enemy.skills if s.skill_id == "furious_roar"), enemy.skills[0])
                # next(제너레이터, 기본값): 조건에 맞는 스킬을 찾으면 그것을, 못 찾으면
                # enemy.skills[0](첫 번째 스킬)을 기본값으로 사용
            elif enemy.name == "부두술사" and not enemy.soul_bound_target and len(self.enemies) > 1:
                # 부두술사는 아직 영혼 결속을 안 걸었고, 다른 적이 한 명 이상 있다면
                # "영혼 결속(soul_bind)" 스킬을 우선 사용
                chosen_skill = next((s for s in enemy.skills if s.skill_id == "soul_bind"), enemy.skills[0])
            else:
                # 특별한 조건에 해당하지 않으면 랜덤으로 스킬 하나를 고름
                chosen_skill = random.choice(enemy.skills)

            # 정해진 행동을 next_actions 딕셔너리에 저장 (나중에 UI 출력 및 실제 행동에 사용)
            self.next_actions[enemy.id] = {
                "unit_name": enemy.name,
                "skill": chosen_skill,
                "target_pos": chosen_skill.target_positions,
                "is_aoe": chosen_skill.is_aoe
            }

    def print_round_ui(self):
        """
        현재 라운드의 상황(아군/적군 체력, 적의 예고된 행동, 행동 순서)을
        콘솔 화면에 보기 좋게 출력하는 함수입니다. (게임 로직에는 영향 없음, 순수 출력용)
        """
        print(f"\n{'='*25} [ ROUND {self.turn_count} ] {'='*25}")

        print("\n[🛡️ 아군 파티]")
        for h in self.heroes:
            st = " [기절]" if h.is_stunned else ""
            # :<5, :>3 같은 표기는 문자열/숫자를 특정 폭에 맞춰 정렬하는 '포맷 지정자'입니다.
            # <는 왼쪽 정렬, >는 오른쪽 정렬을 의미하며 숫자는 최소 칸 수입니다.
            print(f"  {h.position}열: {h.name:<5} | HP: {h.hp:>3}/{h.max_hp:<3} | SPD: {h.get_effective_spd():>2}{st}")

        print("\n[👾 적군 파티]")
        for e in self.enemies:
            st = " [기절]" if e.is_stunned else ""
            print(f"  {e.position}열: {e.name:<6} | HP: {e.hp:>3}/{e.max_hp:<3} | SPD: {e.get_effective_spd():>2}{st}")

        # 적의 다음 행동을 미리 보여주는 UI (일종의 '예고' 시스템으로, 플레이어가 대응 전략을 짤 수 있게 함)
        print("\n🔮 [적 행동 예고 (next_actions)]")
        for enemy_id, act in self.next_actions.items():
            skill: Skill = act["skill"]
            area_txt = "전체 광역" if skill.is_aoe else f"{skill.target_positions}열 공격"
            print(f"  • {act['unit_name']} ➔ 스킬: [{skill.name}] ({area_txt})")

        # 이번 라운드에 행동할 순서를 속도가 빠른 순으로 나열해서 보여줌
        print("\n[⚡ 행동 순서]: " + " ➔ ".join([f"{u.name}({u.get_effective_spd()})" for u in self.turn_order]))
        print("-" * 62)

    def execute_skill(self, user: Entity, skill: Skill, chosen_target: Optional[Entity] = None):
        """
        실제로 스킬 하나를 '사용'하는 핵심 함수입니다.
        user           : 스킬을 사용하는 캐릭터
        skill          : 사용할 스킬 (Skill 객체)
        chosen_target  : 미리 선택된 대상 (단일 대상 스킬일 경우)

        이 함수는 스킬의 target_type에 따라 완전히 다른 동작을 수행합니다.
        위에서부터 순서대로 "해당하는 경우인지" 검사하고, 해당되면 처리 후 return으로 끝냅니다.
        (여러 경우 중 어느 하나에만 해당하도록 설계되어 있습니다.)
        """
        allies = self.heroes if user.team == "player" else self.enemies      # 나와 같은 편
        opponents = self.enemies if user.team == "player" else self.heroes  # 상대 편
        atk_mult = user.get_atk_multiplier()  # 공격력 버프가 적용된 배율을 미리 계산

        self.battle_logs.append(f"▶ [{user.name}]의 [{skill.name}] 시전!")

        # ---- 1. 버프 계열 스킬 처리 ----
        if skill.target_type == "self_buff":
            # 자기 자신에게 버프를 거는 스킬 (예: 전사의 "광폭화")
            user.buffs.append(skill.effect.copy())
            # .copy()를 사용하는 이유: skill.effect를 그대로 참조해서 넣으면,
            # 나중에 duration을 깎을 때 스킬 원본 데이터까지 함께 바뀌어버리는 문제가 생깁니다.
            # 따라서 '복사본'을 만들어서 캐릭터마다 독립적인 버프 데이터를 갖게 합니다.
            self.battle_logs.append(f"  ✨ {user.name} 강화 활성화! ({skill.description})")
            return  # 이 스킬의 처리는 여기서 끝 (아래 공격 로직으로 넘어가지 않음)

        if skill.target_type == "all_allies_buff":
            # 아군 전체에게 버프를 거는 스킬 (예: 마법사의 "시간왜곡")
            for a in allies:
                a.buffs.append(skill.effect.copy())  # 아군 각각에게 독립된 복사본을 부여
            self.battle_logs.append(f"  ⏳ 아군 전체 강화 완료! ({skill.description})")
            return

        if skill.target_type == "all_allies_heal":
            # 아군 전체를 회복시키는 스킬 (예: 지원가의 "정화의 성역")
            for a in allies:
                h_amt = a.heal(random.randint(skill.min_dmg, skill.max_dmg))
                # random.randint(최소, 최대): 최소~최대 사이의 정수를 무작위로 하나 뽑음 (양 끝값 포함)
                self.battle_logs.append(f"  💖 {a.name} HP +{h_amt} 회복 (현재: {a.hp}/{a.max_hp})")
            return

        if skill.target_type == "ally_heal" and chosen_target:
            # 아군 한 명을 지정해서 회복시키는 스킬 (예: 지원가의 "빛의 세례")
            h_amt = chosen_target.heal(random.randint(skill.min_dmg, skill.max_dmg))
            self.battle_logs.append(f"  💖 {chosen_target.name} HP +{h_amt} 회복!")
            return

        if skill.skill_id == "soul_bind":
            # 부두술사 전용 특수 스킬: 살아있는 다른 아군 중 한 명을 무작위로 골라
            # 자신에게 오는 피해의 절반을 대신 받게 만드는 '연결'을 설정
            other_allies = [a for a in allies if a != user and a.is_alive()]
            if other_allies:
                user.soul_bound_target = random.choice(other_allies)
                self.battle_logs.append(f"  💀 {user.name}이(가) {user.soul_bound_target.name}에게 피해 전이 연결!")
            return

        # ---- 2. 공격 대상 확정 (광역 vs 단일) ----
        targets: List[Entity] = []
        if skill.is_aoe:
            # 광역 스킬: target_positions가 지정되어 있으면 그 열의 상대만,
            # 비어있으면([]) 상대 전체를 대상으로 함
            targets = [t for t in opponents if not skill.target_positions or t.position in skill.target_positions]
        elif chosen_target:
            # 단일 대상 스킬: 미리 정해진 chosen_target 한 명만 대상
            targets = [chosen_target]

        # ---- 3. 공격 실행 (대상 각각에게 명중/피해/부가효과 적용) ----
        for t in targets:
            # ---- 명중 판정 ----
            # 최종 명중률 = 스킬의 기본 명중률 - 상대가 가진 명중 회피 관련 디버프
            # max(0.05, ...) : 아무리 낮아도 최소 5%의 확률로는 맞을 수 있게 하는 안전장치
            final_acc = max(0.05, skill.accuracy - user.get_accuracy_modifier())
            if random.random() <= final_acc:
                # random.random()은 0.0 이상 1.0 미만의 난수를 반환합니다.
                # 이 값이 명중률보다 작거나 같으면 "명중"으로 처리
                base_dmg = random.randint(skill.min_dmg, skill.max_dmg) if skill.max_dmg > 0 else skill.min_dmg
                # 데미지 범위가 있다면(max_dmg > 0) 그 범위 내에서 무작위로,
                # 아니라면(예: 상태이상만 주는 스킬) min_dmg 값을 그대로 사용
                dealt = t.take_damage(int(base_dmg * atk_mult), opponents, self.battle_logs)
                # 실제 피해 = 기본 피해 * 공격력 배율. take_damage 내부에서 방어력 등이 추가로 계산됨
                self.battle_logs.append(f"  💥 {t.name}에게 {dealt} 피해! (남은 HP: {t.hp}/{t.max_hp})")

                # ---- 스턴(기절) 판정 ----
                if skill.stun_chance > 0 and random.random() <= skill.stun_chance:
                    t.is_stunned = True
                    self.battle_logs.append(f"    💫 {t.name} 기절!")

                # ---- 출혈 효과 부여 ----
                if skill.effect.get("type") == "bleed" and random.random() <= skill.effect.get("chance", 1.0):
                    t.status_effects.append({"type": "bleed", "damage": skill.effect["damage"], "duration": skill.effect["duration"]})
                    self.battle_logs.append(f"    🩸 {t.name}에게 출혈 부여 ({skill.effect['duration']}턴 지속)!")

                # ---- 디버프(방어력/명중률/속도 감소) 부여 ----
                if skill.effect.get("type") in ["def_down", "acc_down", "spd_down"]:
                    t.debuffs.append(skill.effect.copy())  # 여기서도 원본 훼손을 막기 위해 copy() 사용
                    self.battle_logs.append(f"    📉 {t.name}에게 디버프 부여 ({skill.effect['type']})!")

                # ---- 사용자 자가 회복 효과 (예: 지원가의 "신의 심판") ----
                if skill.effect.get("type") == "self_heal":
                    healed = user.heal(skill.effect["value"])
                    self.battle_logs.append(f"    ✨ {user.name} 체력 {healed} 자가 회복!")

                # ---- 밀쳐내기 / 당기기 효과 ----
                if skill.position_shift != 0:
                    self.shift_entity_position(opponents, t, skill.position_shift)
            else:
                # 명중 판정에 실패한 경우: 아무 효과도 적용하지 않고 "빗나감"만 기록
                self.battle_logs.append(f"  ❌ {t.name}에게 빗나갔습니다!")

    def select_player_action(self, hero: Entity) -> tuple[Skill, Optional[Entity]]:
        """
        플레이어(사람)가 콘솔 입력을 통해 이번 턴에 사용할 스킬과 대상을 고르는 함수입니다.
        input()으로 키보드 입력을 받고, 잘못된 입력이면 계속 다시 물어봅니다(while True 반복문).
        반환값: (선택한 스킬, 선택한 대상) 튜플. 대상이 필요 없는 스킬이면 대상은 None.
        """
        while True:  # 올바른 입력을 받을 때까지 무한 반복
            print(f"\n👉 [{hero.name}] (HP: {hero.hp}/{hero.max_hp}) 스킬 선택:")
            for i, s in enumerate(hero.skills, 1):
                # enumerate(리스트, 1) : 순번을 0이 아닌 1부터 세도록 지정 (사람에게 보여줄 번호이므로)
                pos_txt = f"{s.target_positions}열" if s.target_positions else "자신/전체"
                print(f"  [{i}] {s.name:<8} | 타깃: {pos_txt:<6} | {s.description}")

            sel = input("  스킬 번호를 입력하세요: ").strip()
            # .strip()은 입력값 앞뒤의 불필요한 공백을 제거하는 함수
            if not (sel.isdigit() and 1 <= int(sel) <= len(hero.skills)):
                # isdigit(): 문자열이 숫자로만 이루어져 있는지 확인 (음수/소수 입력 방지)
                # 범위를 벗어나거나 숫자가 아니면 다시 입력받도록 continue
                print("  잘못된 입력입니다.")
                continue

            chosen_skill = hero.skills[int(sel) - 1]  # 사람은 1번부터 세지만 리스트는 0번부터 시작하므로 -1

            # ---- 상대를 지정해야 하는 '단일 공격' 스킬인 경우 ----
            if chosen_skill.target_type == "enemy" and not chosen_skill.is_aoe:
                valid_targets = [e for e in self.enemies if not chosen_skill.target_positions or e.position in chosen_skill.target_positions]
                # 스킬의 사거리(target_positions) 안에 들어오는 적만 고를 수 있음
                if not valid_targets:
                    print("  ⚠️ 사거리 내에 대상이 없습니다. 다른 스킬을 고르세요.")
                    continue  # 처음(스킬 선택)부터 다시

                print("  [공격 대상 선택]")
                for vt in valid_targets:
                    print(f"    [{vt.position}] {vt.name} (HP: {vt.hp}/{vt.max_hp})")
                t_sel = input("  대상 열 번호 입력: ").strip()
                target_entity = next((e for e in valid_targets if str(e.position) == t_sel), None)
                # 입력한 열 번호와 일치하는 적을 찾음. 없으면 None
                if not target_entity:
                    print("  유효하지 않은 대상입니다.")
                    continue
                return chosen_skill, target_entity  # 스킬과 대상을 함께 반환하고 함수 종료

            # ---- 아군을 지정해서 회복시키는 스킬인 경우 ----
            elif chosen_skill.target_type == "ally_heal":
                print("  [치유 대상 선택]")
                for h in self.heroes:
                    print(f"    [{h.position}] {h.name} (HP: {h.hp}/{h.max_hp})")
                h_sel = input("  아군 열 번호 입력: ").strip()
                target_entity = next((h for h in self.heroes if str(h.position) == h_sel), None)
                if not target_entity:
                    print("  유효하지 않은 아군입니다.")
                    continue
                return chosen_skill, target_entity

            # ---- 그 외(자기 버프, 전체 대상 스킬 등 대상 지정이 필요 없는 경우) ----
            return chosen_skill, None

    def start_battle_loop(self):
        """
        전투의 '메인 루프(반복문)'입니다.
        아군과 적군이 모두 한 명 이상 살아있는 동안, 라운드를 계속 반복합니다.
        하나의 라운드 안에서 일어나는 일:
          1) 적의 행동 계획 세우기 + 행동 순서(속도순) 정하기
          2) 현재 상황을 화면에 출력
          3) 정해진 순서대로 각 캐릭터가 실제로 행동 (플레이어는 입력, 적은 AI)
          4) 라운드가 끝나면 버프/디버프 지속시간 감소
        """
        while self.heroes and self.enemies:
            # 파이썬에서 리스트는 비어있지 않으면 True로 취급되므로,
            # "아군도 있고 적도 있는 동안" 이라는 뜻이 됩니다.

            # ---- 1. 라운드 준비: 적 행동(next_actions) 계획 및 턴 순서 정렬 ----
            self.plan_enemy_actions()

            all_units = self.heroes + self.enemies  # 아군 + 적군을 하나의 리스트로 합침
            self.turn_order = sorted(all_units, key=lambda u: (u.get_effective_spd(), random.random()), reverse=True)
            # sorted(..., key=..., reverse=True) : 정렬 기준(key)에 따라 내림차순(속도가 높은 순)으로 정렬
            # key로 (속도, 무작위값) 튜플을 사용하는 이유: 만약 속도가 완전히 같은 캐릭터가 있으면
            # 매번 같은 순서로만 정렬되어 불공평해지므로, 무작위 값을 살짝 더해 순서를 섞어줍니다.
            self.action_queue = [{"entity": u, "spd": u.get_effective_spd()} for u in self.turn_order]
            # 실제 행동 처리에 사용할 큐(queue, 순서가 있는 목록)를 생성

            # ---- 2. UI 표시 ----
            self.print_round_ui()

            # ---- 3. 턴 큐 순회 실행 ----
            for item in self.action_queue:
                unit: Entity = item["entity"]
                if not unit.is_alive() or not self.heroes or not self.enemies:
                    # 이미 죽었거나, 도중에 한쪽 팀이 전멸했다면 더 이상 행동을 진행하지 않고 건너뜀
                    continue

                self.battle_logs.clear()  # 이번 캐릭터의 행동을 기록할 로그를 새로 시작

                # ---- 드래곤의 '폭주' 특수 규칙: 체력 30% 이하면 한 턴에 2번 행동 ----
                action_repeats = 2 if (unit.name == "드래곤" and unit.hp <= unit.max_hp * 0.3) else 1

                for rep in range(action_repeats):
                    # range(1) 이면 한 번만, range(2) 면 두 번 반복 (드래곤 폭주 시)
                    if rep == 0:
                        # 첫 번째 행동에서는 턴 시작 처리(출혈 피해, 기절 확인)를 정상적으로 수행
                        can_act = unit.process_start_of_turn(self.battle_logs)
                    else:
                        # 드래곤의 추가 행동(2번째)에서는 굳이 턴 시작 처리를 다시 하지 않고
                        # 그냥 살아있는지만 확인
                        can_act = unit.is_alive()
                        if can_act:
                            self.battle_logs.append("🔥 [드래곤 폭주] 추가 연속 행동을 개시합니다!")

                    if can_act:
                        if unit.team == "player":
                            # ---- 아군(사람) 차례 ----
                            # 지금까지 쌓인 로그를 먼저 화면에 출력해서 상황을 보여준 뒤
                            for log in self.battle_logs:
                                print(log)
                            self.battle_logs.clear()

                            skill, target = self.select_player_action(unit)  # 사람에게 입력받기
                            self.execute_skill(unit, skill, target)          # 실제로 스킬 실행
                        else:
                            # ---- 적(AI) 차례 ----
                            act_info = self.next_actions.get(unit.id)
                            # 아까 plan_enemy_actions()에서 미리 정해둔 행동을 그대로 사용
                            skill = act_info["skill"] if act_info else random.choice(unit.skills)
                            # 혹시 미리 계획된 행동이 없다면(예외 상황 대비) 무작위로 스킬 선택

                            target = None
                            if skill.target_type == "enemy" and not skill.is_aoe:
                                # 단일 대상 공격 스킬이면 사거리 내의 아군 중 무작위로 한 명 선택
                                valid = [h for h in self.heroes if not skill.target_positions or h.position in skill.target_positions]
                                target = random.choice(valid) if valid else (self.heroes[0] if self.heroes else None)
                                # 사거리 내에 아무도 없으면 그냥 첫 번째 아군을 대상으로 함 (예외 방지용 안전장치)

                            self.execute_skill(unit, skill, target)

                        self.clean_dead()  # 행동 결과로 누군가 죽었을 수 있으니 정리

                    # 이번 행동(rep)에서 쌓인 로그를 모두 화면에 출력
                    for log in self.battle_logs:
                        print(log)
                    self.battle_logs.clear()

                    if not self.heroes or not self.enemies:
                        # 한쪽 팀이 전멸했다면 더 이상의 반복(드래곤 2연속 행동 등)도 멈춤
                        break

            # ---- 4. 라운드 종료: 버프/디버프 지속시간 삭감 ----
            for u in self.heroes + self.enemies:
                u.tick_effects()  # 모든 생존 캐릭터의 버프/디버프 지속 턴을 1씩 감소
            self.clean_dead()     # 혹시 라운드 종료 시점에 죽은 캐릭터가 있다면 정리
            self.turn_count += 1  # 다음 라운드로 넘어감

        # ---- 전투 종료 처리 (while 반복문을 빠져나온 뒤 실행됨) ----
        self.game_state = "GAME_OVER"
        print(f"\n{'='*25} [ 전투 종료 ] {'='*25}")
        if self.heroes:
            # 아군이 한 명이라도 남아있다면 승리
            print("🏆 던전 클리어! 아군 파티가 살아남았습니다!")
        else:
            # 아군이 전멸했다면 패배
            print("💀 전멸... 원정에 실패했습니다.")


# ==========================================
# 데이터 팩토리 (초기 데이터 셋팅)
# ==========================================
# '팩토리(factory)' 함수란, 복잡한 객체를 만드는 과정을 하나의 함수로 묶어서
# 필요할 때마다 간편하게 "찍어낼 수 있게" 해주는 함수를 말합니다.
# 여기서는 아군 파티를 만드는 함수와, 적 파티를 만드는 함수가 있습니다.

def create_hero_party() -> List[Entity]:
    """플레이어가 사용할 아군 파티(전사, 마법사, 지원가) 3명을 생성해서 리스트로 반환합니다."""

    # 1. 전사 : 앞줄에서 싸우는 근접 딜러. 체력이 높고 상대를 밀쳐내는 스킬을 가짐
    warrior = Entity("warrior", "전사", 180, 8, "player")
    warrior.skills = [
        Skill("bone_cleave", "뼈가르기", target_positions=[1, 2], min_dmg=30, max_dmg=30, accuracy=0.80, position_shift=1, description="30 피해, 밀쳐내기, 명중 80%"),
        Skill("whirlwind", "회전 격멸", target_positions=[], is_aoe=True, min_dmg=20, max_dmg=20, accuracy=0.70, description="전체 20 피해 광역, 명중 70%"),
        Skill("demoralizing_roar", "전율의 표효", target_positions=[1, 2, 3, 4], effect={"type": "def_down", "value": 0.25, "duration": 2}, description="단일 방어력 25% 감소 (2턴)"),
        Skill("berserk", "광폭화", target_positions=[], target_type="self_buff", effect={"type": "atk_up", "value": 0.20, "duration": 2}, description="자신 공격력 20% 증가 (2턴)")
    ]

    # 2. 마법사 : 원거리 스킬 딜러. 체력은 낮지만 속도가 빠르고 강력한 광역기를 가짐
    mage = Entity("mage", "마법사", 90, 15, "player")
    mage.skills = [
        Skill("fireball", "파이어볼", target_positions=[2, 3, 4], min_dmg=20, max_dmg=40, accuracy=0.80, description="2~4열 20~40 피해, 명중 80%"),
        Skill("chain_lightning", "체인라이트닝", target_positions=[1, 2], min_dmg=5, max_dmg=15, stun_chance=0.65, description="1~2열 5~15 피해, 65% 스턴"),
        Skill("time_warp", "시간왜곡", target_positions=[], target_type="all_allies_buff", effect={"type": "spd_up", "value": 5, "duration": 2}, description="아군 전체 SPD +5 (2턴)"),
        Skill("armageddon", "아마겟돈", target_positions=[], is_aoe=True, min_dmg=100, max_dmg=100, accuracy=0.10, description="전체 100 피해 광역, 명중 10%")
        # 명중률이 10%로 매우 낮은 대신, 맞으면 100의 고정 피해를 주는 '하이리스크 하이리턴' 스킬입니다.
    ]

    # 3. 지원가 : 아군을 회복시키는 힐러. 필요하면 약간의 공격/제어기도 사용 가능
    priest = Entity("priest", "지원가", 120, 12, "player")
    priest.skills = [
        Skill("holy_judgment", "신의 심판", target_positions=[1, 2], min_dmg=15, max_dmg=25, effect={"type": "self_heal", "value": 10}, description="1~2열 15~25 피해 + 자신 10 치유"),
        Skill("light_baptism", "빛의 세례", target_positions=[], target_type="ally_heal", min_dmg=20, max_dmg=40, description="아군 단일 20~40 치유"),
        Skill("sanctuary", "정화의 성역", target_positions=[], target_type="all_allies_heal", min_dmg=10, max_dmg=20, description="아군 전체 10~20 치유"),
        Skill("thorn_vines", "가시덩굴", target_positions=[1, 2, 3, 4], min_dmg=5, max_dmg=5, stun_chance=0.70, position_shift=-1, description="5 피해, 1열로 당기기, 70% 스턴")
    ]
    return [warrior, mage, priest]


def create_enemy_encounter(choice: str) -> List[Entity]:
    """
    플레이어가 고른 번호(choice)에 따라 서로 다른 적 인카운터(전투 상대)를 생성합니다.
    choice == "2" : 골렘(중간 보스) 1마리
    choice == "3" : 드래곤(최종 보스) 1마리
    그 외(기본값)  : 오크, 늑대, 고블린, 부두술사로 이루어진 일반 몬스터 4마리
    """
    if choice == "2":  # 골렘
        golem = Entity("golem", "골렘", 350, 5, "enemy", is_boss=True)
        golem.skills = [
            Skill("rock_fall", "암석 낙하", target_positions=[1, 2], is_aoe=True, min_dmg=20, max_dmg=35, accuracy=0.50),
            Skill("seismic_wave", "지진파", target_positions=[], is_aoe=True, min_dmg=5, max_dmg=5, accuracy=0.70, effect={"type": "spd_down", "value": 8, "duration": 2}),
            Skill("rock_skin", "바위 피부", target_positions=[], target_type="self_buff", effect={"type": "def_up", "value": 0.10, "duration": 2})
        ]
        return [golem]  # 반환값은 항상 List[Entity] 형태이므로, 한 마리여도 리스트로 감싸서 반환

    if choice == "3":  # 드래곤
        dragon = Entity("dragon", "드래곤", 800, 13, "enemy", is_boss=True)
        dragon.skills = [
            Skill("fire_breath", "화염 브레스", target_positions=[], is_aoe=True, min_dmg=20, max_dmg=40, accuracy=0.60),
            Skill("dragon_claw", "용의 발톱", target_positions=[1], min_dmg=45, max_dmg=45, accuracy=0.70),
            Skill("dragon_roar", "용의 포효", target_positions=[], is_aoe=True, stun_chance=0.40)
            # 이 스킬은 min_dmg/max_dmg가 지정되지 않아(둘 다 0) 데미지 없이 기절만 노리는 스킬입니다.
        ]
        return [dragon]

    # 기본값 (choice가 "1"이거나 그 외 값일 때): 일반 몬스터 4인방
    orc = Entity("orc_1", "오크", 80, 7, "enemy")
    orc.skills = [
        Skill("club_strike", "몽둥이 내리치기", target_positions=[1, 2], min_dmg=25, max_dmg=35, stun_chance=0.20),
        Skill("furious_roar", "분노의 함성", target_positions=[], target_type="self_buff", effect={"type": "atk_up", "value": 0.25, "duration": 99})
        # duration=99 처럼 매우 큰 값을 넣어서 사실상 "전투가 끝날 때까지 지속되는" 버프처럼 동작하게 만든 트릭입니다.
    ]

    wolf = Entity("wolf_1", "늑대", 45, 16, "enemy")
    wolf.skills = [
        Skill("neck_bite", "목덜미 물어뜯기", target_positions=[1, 2, 3, 4], min_dmg=15, max_dmg=20, effect={"type": "bleed", "damage": 5, "duration": 2, "chance": 0.40}),
        Skill("howling", "하울링", target_positions=[], target_type="all_allies_buff", effect={"type": "atk_up", "value": 0.10, "duration": 2})
    ]

    goblin = Entity("goblin_1", "고블린", 35, 14, "enemy")
    goblin.skills = [
        Skill("dagger_stab", "단검 찌르기", target_positions=[1, 2], min_dmg=10, max_dmg=15),
        Skill("sand_throw", "모래 뿌리기", target_positions=[1, 2, 3, 4], effect={"type": "acc_down", "value": 0.30, "duration": 2})
    ]

    voodoo = Entity("voodoo_1", "부두술사", 50, 11, "enemy")
    voodoo.skills = [
        Skill("curse_of_decay", "부패의 저주", target_positions=[2, 3], is_aoe=True, min_dmg=15, max_dmg=35),
        Skill("soul_bind", "영혼 결속", target_positions=[], target_type="special")
    ]

    return [orc, wolf, goblin, voodoo]


# ==========================================
# 실행부
# ==========================================
# if __name__ == "__main__": 은 파이썬의 대표적인 관례입니다.
# 이 파일을 '직접 실행'했을 때만 아래 코드가 동작하고,
# 만약 이 파일을 다른 파이썬 코드에서 import(불러오기) 했을 때는
# 아래 코드가 자동으로 실행되지 않도록 막아주는 역할을 합니다.
if __name__ == "__main__":
    print("전투에 진입할 인카운터를 선택하세요:")
    print("1. 일반 몬스터 (오크, 늑대, 고블린, 부두술사)")
    print("2. 중간 보스 (골렘)")
    print("3. 최종 보스 (드래곤)")
    user_choice = input("선택 (1/2/3): ").strip()

    heroes = create_hero_party()               # 아군 파티 생성
    enemies = create_enemy_encounter(user_choice)  # 선택에 따른 적 파티 생성

    battle = BattleManager(heroes, enemies)     # 전투 진행자(매니저) 객체 생성
    battle.start_battle_loop()                  # 전투 시작! (모든 라운드가 끝날 때까지 이 함수 안에서 진행됨)
