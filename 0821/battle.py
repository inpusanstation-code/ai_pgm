#전투 시스템 (공통 변수 적용)
import random
from typing import List, Dict, Optional, Any

# ==========================================
# 3. 스킬 및 행동 데이터 모델 (Skill System)
# ==========================================
class Skill:
    def __init__(
        self,
        skill_id: str,
        name: str,
        target_positions: List[int],
        is_aoe: bool = False,
        min_dmg: int = 0,
        max_dmg: int = 0,
        accuracy: float = 1.0,
        stun_chance: float = 0.0,
        position_shift: int = 0,  # +1: 밀쳐내기(뒤로), -1: 당기기(앞으로)
        target_type: str = "enemy",  # "enemy", "ally", "self", "all_allies"
        effect: Optional[Dict[str, Any]] = None,
        description: str = ""
    ):
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
        self.effect = effect or {}
        self.description = description


# ==========================================
# 2. 엔티티 데이터 모델 (Entity Model)
# ==========================================
class Entity:
    def __init__(self, id_str: str, name: str, max_hp: int, spd: int, team: str, is_boss: bool = False):
        self.id: str = id_str
        self.name: str = name
        self.max_hp: int = max_hp
        self.hp: int = max_hp
        self.spd: int = spd
        self.team: str = team  # "player" or "enemy"
        self.is_boss: bool = is_boss
        self.position: int = 1  # 1 ~ 4열 (1-based)

        self.is_stunned: bool = False
        self.buffs: List[Dict[str, Any]] = []           # [{"type": "atk_up", "value": 0.2, "duration": 2}]
        self.debuffs: List[Dict[str, Any]] = []         # [{"type": "def_down", "value": 0.25, "duration": 2}]
        self.status_effects: List[Dict[str, Any]] = []  # [{"type": "bleed", "damage": 5, "duration": 2}]
        self.soul_bound_target: Optional['Entity'] = None

        self.skills: List[Skill] = []

    def is_alive(self) -> bool:
        return self.hp > 0

    def get_effective_spd(self) -> int:
        spd_val = self.spd
        for b in self.buffs:
            if b.get("type") == "spd_up":
                spd_val += int(b.get("value", 0))
        for d in self.debuffs:
            if d.get("type") == "spd_down":
                spd_val -= int(d.get("value", 0))
        return max(1, spd_val)

    def get_atk_multiplier(self) -> float:
        mult = 1.0
        for b in self.buffs:
            if b.get("type") == "atk_up":
                mult += float(b.get("value", 0.0))
        return mult

    def get_accuracy_modifier(self) -> float:
        mod = 0.0
        for d in self.debuffs:
            if d.get("type") == "acc_down":
                mod += float(d.get("value", 0.0))
        return mod

    def take_damage(self, raw_dmg: int, team_entities: List['Entity'], logs: List[str]) -> int:
        if not self.is_alive():
            return 0

        # 방어 계산
        def_mod = 1.0
        for b in self.buffs:
            if b.get("type") == "def_up":
                def_mod -= float(b.get("value", 0.0))
        for d in self.debuffs:
            if d.get("type") == "def_down":
                def_mod += float(d.get("value", 0.0))
        
        final_dmg = int(raw_dmg * max(0.1, def_mod))

        # 부두술사 영혼 결속 판정
        if self.soul_bound_target and self.soul_bound_target.is_alive() and (self.soul_bound_target in team_entities):
            transfer_dmg = int(final_dmg * 0.5)
            final_dmg -= transfer_dmg
            self.soul_bound_target.hp = max(0, self.soul_bound_target.hp - transfer_dmg)
            logs.append(f"  🔗 [영혼 결속] {self.soul_bound_target.name}이(가) {transfer_dmg}의 피해를 대신 흡수했습니다!")

        self.hp = max(0, self.hp - final_dmg)
        return final_dmg

    def heal(self, amount: int) -> int:
        if not self.is_alive():
            return 0
        actual = min(self.max_hp - self.hp, amount)
        self.hp += actual
        return actual

    def process_start_of_turn(self, logs: List[str]) -> bool:
        # 1. 상태이상(출혈 등)
        rem_status = []
        for s in self.status_effects:
            if s.get("type") == "bleed":
                dmg = s.get("damage", 0)
                self.hp = max(0, self.hp - dmg)
                logs.append(f"🩸 {self.name}이(가) 출혈로 {dmg}의 피해를 입었습니다! (HP: {self.hp}/{self.max_hp})")
                s["duration"] -= 1
                if s["duration"] > 0:
                    rem_status.append(s)
        self.status_effects = rem_status

        # 2. 스턴 체크
        if self.is_stunned:
            self.is_stunned = False
            logs.append(f"💫 {self.name}은(는) 기절에서 깨어났지만 턴을 소모합니다!")
            return False
        return self.is_alive()

    def tick_effects(self):
        # 버프/디버프 지속 턴 감소
        self.buffs = [b for b in self.buffs if self._decrement(b)]
        self.debuffs = [d for d in self.debuffs if self._decrement(d)]

    @staticmethod
    def _decrement(effect_dict: Dict[str, Any]) -> bool:
        effect_dict["duration"] -= 1
        return effect_dict["duration"] > 0


# ==========================================
# 1 & 4. 전투 시스템 및 게임 매니저 (Battle System)
# ==========================================
class BattleManager:
    def __init__(self, heroes: List[Entity], enemies: List[Entity]):
        # 1. 전역 상태 관리 변수
        self.current_node: int = 1
        self.game_state: str = "BATTLE"
        self.turn_count: int = 1
        self.turn_order: List[Entity] = []

        # 4. 전투 연산 및 UI 표시 변수
        self.next_actions: Dict[str, Dict[str, Any]] = {}
        self.action_queue: List[Dict[str, Any]] = []
        self.battle_logs: List[str] = []

        self.heroes: List[Entity] = heroes
        self.enemies: List[Entity] = enemies
        self._update_positions()

    def _update_positions(self):
        """배열 순서에 따라 position(1~4열) 갱신"""
        for i, h in enumerate(self.heroes):
            h.position = i + 1
        for i, e in enumerate(self.enemies):
            e.position = i + 1

    def clean_dead(self):
        for h in self.heroes:
            if not h.is_alive():
                self.battle_logs.append(f"💀 아군 [{h.name}]이(가) 쓰러졌습니다!")
        for e in self.enemies:
            if not e.is_alive():
                self.battle_logs.append(f"💥 적 [{e.name}]을(를) 처치했습니다!")

        self.heroes = [h for h in self.heroes if h.is_alive()]
        self.enemies = [e for e in self.enemies if e.is_alive()]
        self._update_positions()

    def shift_entity_position(self, team_list: List[Entity], target_entity: Entity, shift: int):
        """position_shift 적용 (+1 밀쳐내기, -1 맨앞으로 당기기)"""
        if target_entity not in team_list:
            return
        cur_idx = team_list.index(target_entity)
        if shift > 0 and cur_idx + 1 < len(team_list):  # 밀쳐내기 (1열 -> 2열)
            team_list[cur_idx], team_list[cur_idx + 1] = team_list[cur_idx + 1], team_list[cur_idx]
            self.battle_logs.append(f"  ↪️ [밀쳐내기] {target_entity.name}이(가) 뒤로 밀려났습니다!")
        elif shift < 0 and cur_idx > 0:  # 당기기 (1열로 끌어옴)
            team_list.pop(cur_idx)
            team_list.insert(0, target_entity)
            self.battle_logs.append(f"  ↩️ [당기기] {target_entity.name}이(가) 1열로 끌려왔습니다!")
        self._update_positions()

    def plan_enemy_actions(self):
        """매 라운드 시작 시 모든 적의 다음 행동(next_actions) 결정 및 예고"""
        self.next_actions.clear()
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            
            # 스킬 선택 로직
            chosen_skill = None
            if enemy.name == "오크" and enemy.hp <= enemy.max_hp * 0.5 and not any(b.get("type") == "atk_up" for b in enemy.buffs):
                chosen_skill = next((s for s in enemy.skills if s.skill_id == "furious_roar"), enemy.skills[0])
            elif enemy.name == "부두술사" and not enemy.soul_bound_target and len(self.enemies) > 1:
                chosen_skill = next((s for s in enemy.skills if s.skill_id == "soul_bind"), enemy.skills[0])
            else:
                chosen_skill = random.choice(enemy.skills)

            self.next_actions[enemy.id] = {
                "unit_name": enemy.name,
                "skill": chosen_skill,
                "target_pos": chosen_skill.target_positions,
                "is_aoe": chosen_skill.is_aoe
            }

    def print_round_ui(self):
        print(f"\n{'='*25} [ ROUND {self.turn_count} ] {'='*25}")
        
        print("\n[🛡️ 아군 파티]")
        for h in self.heroes:
            st = " [기절]" if h.is_stunned else ""
            print(f"  {h.position}열: {h.name:<5} | HP: {h.hp:>3}/{h.max_hp:<3} | SPD: {h.get_effective_spd():>2}{st}")

        print("\n[👾 적군 파티]")
        for e in self.enemies:
            st = " [기절]" if e.is_stunned else ""
            print(f"  {e.position}열: {e.name:<6} | HP: {e.hp:>3}/{e.max_hp:<3} | SPD: {e.get_effective_spd():>2}{st}")

        # 전체 공격 표시 UI
        print("\n🔮 [적 행동 예고 (next_actions)]")
        for enemy_id, act in self.next_actions.items():
            skill: Skill = act["skill"]
            area_txt = "전체 광역" if skill.is_aoe else f"{skill.target_positions}열 공격"
            print(f"  • {act['unit_name']} ➔ 스킬: [{skill.name}] ({area_txt})")

        print("\n[⚡ 행동 순서]: " + " ➔ ".join([f"{u.name}({u.get_effective_spd()})" for u in self.turn_order]))
        print("-" * 62)

    def execute_skill(self, user: Entity, skill: Skill, chosen_target: Optional[Entity] = None):
        allies = self.heroes if user.team == "player" else self.enemies
        opponents = self.enemies if user.team == "player" else self.heroes
        atk_mult = user.get_atk_multiplier()

        self.battle_logs.append(f"▶ [{user.name}]의 [{skill.name}] 시전!")

        # 1. 버프/특수 스킬
        if skill.target_type == "self_buff":
            user.buffs.append(skill.effect.copy())
            self.battle_logs.append(f"  ✨ {user.name} 강화 활성화! ({skill.description})")
            return

        if skill.target_type == "all_allies_buff":
            for a in allies:
                a.buffs.append(skill.effect.copy())
            self.battle_logs.append(f"  ⏳ 아군 전체 강화 완료! ({skill.description})")
            return

        if skill.target_type == "all_allies_heal":
            for a in allies:
                h_amt = a.heal(random.randint(skill.min_dmg, skill.max_dmg))
                self.battle_logs.append(f"  💖 {a.name} HP +{h_amt} 회복 (현재: {a.hp}/{a.max_hp})")
            return

        if skill.target_type == "ally_heal" and chosen_target:
            h_amt = chosen_target.heal(random.randint(skill.min_dmg, skill.max_dmg))
            self.battle_logs.append(f"  💖 {chosen_target.name} HP +{h_amt} 회복!")
            return

        if skill.skill_id == "soul_bind":
            other_allies = [a for a in allies if a != user and a.is_alive()]
            if other_allies:
                user.soul_bound_target = random.choice(other_allies)
                self.battle_logs.append(f"  💀 {user.name}이(가) {user.soul_bound_target.name}에게 피해 전이 연결!")
            return

        # 2. 공격 대상 확정 (광역 vs 단일)
        targets: List[Entity] = []
        if skill.is_aoe:
            targets = [t for t in opponents if not skill.target_positions or t.position in skill.target_positions]
        elif chosen_target:
            targets = [chosen_target]

        # 3. 공격 실행
        for t in targets:
            # 명중 굴림
            final_acc = max(0.05, skill.accuracy - user.get_accuracy_modifier())
            if random.random() <= final_acc:
                base_dmg = random.randint(skill.min_dmg, skill.max_dmg) if skill.max_dmg > 0 else skill.min_dmg
                dealt = t.take_damage(int(base_dmg * atk_mult), opponents, self.battle_logs)
                self.battle_logs.append(f"  💥 {t.name}에게 {dealt} 피해! (남은 HP: {t.hp}/{t.max_hp})")

                # 스턴 굴림
                if skill.stun_chance > 0 and random.random() <= skill.stun_chance:
                    t.is_stunned = True
                    self.battle_logs.append(f"    💫 {t.name} 기절!")

                # 출혈 등 효과
                if skill.effect.get("type") == "bleed" and random.random() <= skill.effect.get("chance", 1.0):
                    t.status_effects.append({"type": "bleed", "damage": skill.effect["damage"], "duration": skill.effect["duration"]})
                    self.battle_logs.append(f"    🩸 {t.name}에게 출혈 부여 ({skill.effect['duration']}턴 지속)!")

                # 디버프 적용
                if skill.effect.get("type") in ["def_down", "acc_down", "spd_down"]:
                    t.debuffs.append(skill.effect.copy())
                    self.battle_logs.append(f"    📉 {t.name}에게 디버프 부여 ({skill.effect['type']})!")

                # 자힐
                if skill.effect.get("type") == "self_heal":
                    healed = user.heal(skill.effect["value"])
                    self.battle_logs.append(f"    ✨ {user.name} 체력 {healed} 자가 회복!")

                # 밀쳐내기 / 당기기
                if skill.position_shift != 0:
                    self.shift_entity_position(opponents, t, skill.position_shift)
            else:
                self.battle_logs.append(f"  ❌ {t.name}에게 빗나갔습니다!")

    def select_player_action(self, hero: Entity) -> tuple[Skill, Optional[Entity]]:
        while True:
            print(f"\n👉 [{hero.name}] (HP: {hero.hp}/{hero.max_hp}) 스킬 선택:")
            for i, s in enumerate(hero.skills, 1):
                pos_txt = f"{s.target_positions}열" if s.target_positions else "자신/전체"
                print(f"  [{i}] {s.name:<8} | 타깃: {pos_txt:<6} | {s.description}")
            
            sel = input("  스킬 번호를 입력하세요: ").strip()
            if not (sel.isdigit() and 1 <= int(sel) <= len(hero.skills)):
                print("  잘못된 입력입니다.")
                continue

            chosen_skill = hero.skills[int(sel) - 1]

            # 타겟팅이 필요한 단일기 처리
            if chosen_skill.target_type == "enemy" and not chosen_skill.is_aoe:
                valid_targets = [e for e in self.enemies if not chosen_skill.target_positions or e.position in chosen_skill.target_positions]
                if not valid_targets:
                    print("  ⚠️ 사거리 내에 대상이 없습니다. 다른 스킬을 고르세요.")
                    continue
                
                print("  [공격 대상 선택]")
                for vt in valid_targets:
                    print(f"    [{vt.position}] {vt.name} (HP: {vt.hp}/{vt.max_hp})")
                t_sel = input("  대상 열 번호 입력: ").strip()
                target_entity = next((e for e in valid_targets if str(e.position) == t_sel), None)
                if not target_entity:
                    print("  유효하지 않은 대상입니다.")
                    continue
                return chosen_skill, target_entity

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

            return chosen_skill, None

    def start_battle_loop(self):
        while self.heroes and self.enemies:
            # 1. 라운드 준비: 적 행동(next_actions) 계획 및 턴 순서 정렬
            self.plan_enemy_actions()
            
            all_units = self.heroes + self.enemies
            self.turn_order = sorted(all_units, key=lambda u: (u.get_effective_spd(), random.random()), reverse=True)
            self.action_queue = [{"entity": u, "spd": u.get_effective_spd()} for u in self.turn_order]

            # 2. UI 표시
            self.print_round_ui()

            # 3. 턴 큐 순회 실행
            for item in self.action_queue:
                unit: Entity = item["entity"]
                if not unit.is_alive() or not self.heroes or not self.enemies:
                    continue

                self.battle_logs.clear()

                # 용의 폭주 체크 (HP 30% 이하 시 2회 행동)
                action_repeats = 2 if (unit.name == "드래곤" and unit.hp <= unit.max_hp * 0.3) else 1

                for rep in range(action_repeats):
                    if rep == 0:
                        can_act = unit.process_start_of_turn(self.battle_logs)
                    else:
                        can_act = unit.is_alive()
                        if can_act:
                            self.battle_logs.append("🔥 [드래곤 폭주] 추가 연속 행동을 개시합니다!")

                    if can_act:
                        if unit.team == "player":
                            # 콘솔 로그 방출 후 플레이어 입력 받기
                            for log in self.battle_logs:
                                print(log)
                            self.battle_logs.clear()

                            skill, target = self.select_player_action(unit)
                            self.execute_skill(unit, skill, target)
                        else:
                            # 적 AI 행동 실행
                            act_info = self.next_actions.get(unit.id)
                            skill = act_info["skill"] if act_info else random.choice(unit.skills)
                            
                            target = None
                            if skill.target_type == "enemy" and not skill.is_aoe:
                                valid = [h for h in self.heroes if not skill.target_positions or h.position in skill.target_positions]
                                target = random.choice(valid) if valid else (self.heroes[0] if self.heroes else None)

                            self.execute_skill(unit, skill, target)

                        self.clean_dead()

                    # 로그 출력
                    for log in self.battle_logs:
                        print(log)
                    self.battle_logs.clear()

                    if not self.heroes or not self.enemies:
                        break

            # 4. 라운드 종료: 버프/디버프 지속시간 삭감
            for u in self.heroes + self.enemies:
                u.tick_effects()
            self.clean_dead()
            self.turn_count += 1

        # 전투 종료 처리
        self.game_state = "GAME_OVER"
        print(f"\n{'='*25} [ 전투 종료 ] {'='*25}")
        if self.heroes:
            print("🏆 던전 클리어! 아군 파티가 살아남았습니다!")
        else:
            print("💀 전멸... 원정에 실패했습니다.")


# ==========================================
# 데이터 팩토리 (초기 데이터 셋팅)
# ==========================================
def create_hero_party() -> List[Entity]:
    # 1. 전사
    warrior = Entity("warrior", "전사", 180, 8, "player")
    warrior.skills = [
        Skill("bone_cleave", "뼈가르기", target_positions=[1, 2], min_dmg=30, max_dmg=30, accuracy=0.80, position_shift=1, description="30 피해, 밀쳐내기, 명중 80%"),
        Skill("whirlwind", "회전 격멸", target_positions=[], is_aoe=True, min_dmg=20, max_dmg=20, accuracy=0.70, description="전체 20 피해 광역, 명중 70%"),
        Skill("demoralizing_roar", "전율의 표효", target_positions=[1, 2, 3, 4], effect={"type": "def_down", "value": 0.25, "duration": 2}, description="단일 방어력 25% 감소 (2턴)"),
        Skill("berserk", "광폭화", target_positions=[], target_type="self_buff", effect={"type": "atk_up", "value": 0.20, "duration": 2}, description="자신 공격력 20% 증가 (2턴)")
    ]

    # 2. 마법사
    mage = Entity("mage", "마법사", 90, 15, "player")
    mage.skills = [
        Skill("fireball", "파이어볼", target_positions=[2, 3, 4], min_dmg=20, max_dmg=40, accuracy=0.80, description="2~4열 20~40 피해, 명중 80%"),
        Skill("chain_lightning", "체인라이트닝", target_positions=[1, 2], min_dmg=5, max_dmg=15, stun_chance=0.65, description="1~2열 5~15 피해, 65% 스턴"),
        Skill("time_warp", "시간왜곡", target_positions=[], target_type="all_allies_buff", effect={"type": "spd_up", "value": 5, "duration": 2}, description="아군 전체 SPD +5 (2턴)"),
        Skill("armageddon", "아마겟돈", target_positions=[], is_aoe=True, min_dmg=100, max_dmg=100, accuracy=0.10, description="전체 100 피해 광역, 명중 10%")
    ]

    # 3. 지원가
    priest = Entity("priest", "지원가", 120, 12, "player")
    priest.skills = [
        Skill("holy_judgment", "신의 심판", target_positions=[1, 2], min_dmg=15, max_dmg=25, effect={"type": "self_heal", "value": 10}, description="1~2열 15~25 피해 + 자신 10 치유"),
        Skill("light_baptism", "빛의 세례", target_positions=[], target_type="ally_heal", min_dmg=20, max_dmg=40, description="아군 단일 20~40 치유"),
        Skill("sanctuary", "정화의 성역", target_positions=[], target_type="all_allies_heal", min_dmg=10, max_dmg=20, description="아군 전체 10~20 치유"),
        Skill("thorn_vines", "가시덩굴", target_positions=[1, 2, 3, 4], min_dmg=5, max_dmg=5, stun_chance=0.70, position_shift=-1, description="5 피해, 1열로 당기기, 70% 스턴")
    ]
    return [warrior, mage, priest]

def create_enemy_encounter(choice: str) -> List[Entity]:
    if choice == "2":  # 골렘
        golem = Entity("golem", "골렘", 350, 5, "enemy", is_boss=True)
        golem.skills = [
            Skill("rock_fall", "암석 낙하", target_positions=[1, 2], is_aoe=True, min_dmg=20, max_dmg=35, accuracy=0.50),
            Skill("seismic_wave", "지진파", target_positions=[], is_aoe=True, min_dmg=5, max_dmg=5, accuracy=0.70, effect={"type": "spd_down", "value": 8, "duration": 2}),
            Skill("rock_skin", "바위 피부", target_positions=[], target_type="self_buff", effect={"type": "def_up", "value": 0.10, "duration": 2})
        ]
        return [golem]

    if choice == "3":  # 드래곤
        dragon = Entity("dragon", "드래곤", 800, 13, "enemy", is_boss=True)
        dragon.skills = [
            Skill("fire_breath", "화염 브레스", target_positions=[], is_aoe=True, min_dmg=20, max_dmg=40, accuracy=0.60),
            Skill("dragon_claw", "용의 발톱", target_positions=[1], min_dmg=45, max_dmg=45, accuracy=0.70),
            Skill("dragon_roar", "용의 포효", target_positions=[], is_aoe=True, stun_chance=0.40)
        ]
        return [dragon]

    # 기본: 일반 몬스터 4인
    orc = Entity("orc_1", "오크", 80, 7, "enemy")
    orc.skills = [
        Skill("club_strike", "몽둥이 내리치기", target_positions=[1, 2], min_dmg=25, max_dmg=35, stun_chance=0.20),
        Skill("furious_roar", "분노의 함성", target_positions=[], target_type="self_buff", effect={"type": "atk_up", "value": 0.25, "duration": 99})
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
if __name__ == "__main__":
    print("전투에 진입할 인카운터를 선택하세요:")
    print("1. 일반 몬스터 (오크, 늑대, 고블린, 부두술사)")
    print("2. 중간 보스 (골렘)")
    print("3. 최종 보스 (드래곤)")
    user_choice = input("선택 (1/2/3): ").strip()

    heroes = create_hero_party()
    enemies = create_enemy_encounter(user_choice)

    battle = BattleManager(heroes, enemies)
    battle.start_battle_loop()

