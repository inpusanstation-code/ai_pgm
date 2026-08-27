import random
import time
from typing import List, Optional


# ==========================================
# 1. 상점 및 아이템 시스템 (포션 인벤토리 연동)
# ==========================================
class Item:
    QUALITY_PREFIXES = {1: "하급", 2: "일반", 3: "고급", 4: "희귀", 5: "전설"}
    STAT_LABELS = {
        "weapon": "공격력",
        "armor": "방어력",
        "potion": "회복량",
        "necklace": "공격력",
        "ring": "방어력",
    }

    def __init__(
        self,
        name: str,
        item_type: str,
        quality: int,
        effect_value: int,
        price: int,
    ):
        self.quality = quality
        self.name = f"[{self.QUALITY_PREFIXES.get(quality, '일반')}] {name}"
        self.item_type = item_type
        self.effect_value = effect_value
        self.price = price

    def __repr__(self):
        stat_label = self.STAT_LABELS.get(self.item_type, "효과")
        return f"{self.name:<16} | {stat_label} +{self.effect_value:<3} | 가격: {self.price} G"


class Shop:
    SHOP_CATALOGS = {
        "무기 상점": [
            ("나무 몽둥이", "weapon", 1, 6, 45),
            ("초보의 검", "weapon", 2, 12, 110),
            ("전사의 대검", "weapon", 3, 23, 230),
            ("파괴검", "weapon", 4, 36, 420),
            ("창세검", "weapon", 5, 70, 950),
        ],
        "방어구 상점": [
            ("천 조끼", "armor", 1, 3, 40),
            ("가죽 흉갑", "armor", 2, 8, 100),
            ("기사의 갑주", "armor", 3, 16, 220),
            ("용비늘 갑주", "armor", 4, 34, 520),
            ("신성갑", "armor", 5, 58, 950),
        ],
        "포션 상점": [
            ("응급 붕대", "potion", 1, 25, 40),
            ("치유 물약", "potion", 2, 55, 100),
            ("푸른 영약", "potion", 3, 95, 210),
            ("치유 성배", "potion", 4, 125, 300),
            ("생명수", "potion", 5, 300, 850),
        ],
        "떠돌이 잡상인": [
            ("구리 목걸이", "necklace", 1, 2, 50),
            ("싸구려 반지", "ring", 2, 4, 90),
            ("수호 반지", "ring", 3, 7, 160),
            ("용의 비늘 반지", "ring", 4, 11, 280),
            ("신왕의 반지", "ring", 5, 18, 500),
        ],
    }

    def __init__(self, shop_type: str):
        if shop_type not in self.SHOP_CATALOGS:
            raise ValueError(f"존재하지 않는 상점 종류입니다: {shop_type}")
        self.shop_type = shop_type
        self.inventory = self._build_inventory()

    def _build_inventory(self) -> List[Item]:
        return [Item(*args) for args in self.SHOP_CATALOGS[self.shop_type]]

    def display_goods(self):
        print(f"\n{'='*15} [ {self.shop_type} ] {'='*15}")
        for idx, item in enumerate(self.inventory, 1):
            print(f"[{idx:2d}] {item}")
        print("=" * 48)

    def process_transaction(self, run_manager, choice_index: int) -> bool:
        if choice_index < 0 or choice_index >= len(self.inventory):
            print("\n[오류] 존재하지 않는 상품입니다.")
            return False

        target_item = self.inventory[choice_index]
        if run_manager.gold < target_item.price:
            print(f"\n[구매 실패] 골드가 부족합니다! (소지: {run_manager.gold} G)")
            return False

        # 소비 아이템(포션)은 인벤토리에 보관
        if target_item.item_type == "potion":
            run_manager.gold -= target_item.price
            run_manager.inventory.append(target_item)
            print(
                f"\n[구매 완료] {target_item.name}을(를) 가방에 넣었습니다! (전투 중 사용 가능)"
            )
            return True

        # 장비 아이템은 영웅에게 즉시 장착
        print("\n누구에게 장착하시겠습니까?")
        for i, h in enumerate(run_manager.heroes, 1):
            print(
                f"  [{i}] {h.name} (추가공격: {h.bonus_atk}, 추가방어: {h.bonus_def})"
            )
        print("  [0] 취소")

        while True:
            sel = input("선택: ").strip()
            if sel == "0":
                return False
            if sel.isdigit() and 1 <= int(sel) <= len(run_manager.heroes):
                target_hero = run_manager.heroes[int(sel) - 1]
                break
            print("올바른 번호를 입력하세요.")

        run_manager.gold -= target_item.price
        run_manager.inventory.append(target_item)  # 소지품 기록용

        if target_item.item_type in ["weapon", "necklace"]:
            target_hero.bonus_atk += target_item.effect_value
            print(
                f"\n[장착 완료] {target_hero.name}의 공격력이 {target_item.effect_value} 증가했습니다!"
            )
        elif target_item.item_type in ["armor", "ring"]:
            target_hero.bonus_def += target_item.effect_value
            print(
                f"\n[장착 완료] {target_hero.name}의 방어력이 {target_item.effect_value} 증가했습니다!"
            )
        return True


def enter_shop_loop(run_manager):
    shop_menu = {
        "1": "무기 상점",
        "2": "방어구 상점",
        "3": "포션 상점",
        "4": "떠돌이 잡상인",
    }
    while True:
        print(f"\n========== 마을 상가 (소지 골드: {run_manager.gold} G) ==========")
        for k, v in shop_menu.items():
            print(f"{k}. {v}")
        print("0. 마을로 돌아가기 (상점 종료)")

        shop_choice = input("상점 선택: ").strip()
        if shop_choice == "0":
            break
        if shop_choice not in shop_menu:
            print("올바른 상점 번호를 입력하세요.")
            continue

        shop = Shop(shop_menu[shop_choice])
        while True:
            shop.display_goods()
            user_input = input("구매할 아이템 번호 (0: 뒤로가기): ").strip()
            if user_input == "0":
                break
            if user_input.isdigit():
                shop.process_transaction(run_manager, int(user_input) - 1)
            else:
                print("아이템 번호를 숫자로 입력하세요.")


# ==========================================
# 2. 스킬 및 엔티티 모델
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
        position_shift: int = 0,
        target_type: str = "enemy",
        effect: dict = None,
        description: str = "",
    ):
        self.skill_id, self.name, self.target_positions = (
            skill_id,
            name,
            target_positions,
        )
        self.is_aoe, self.min_dmg, self.max_dmg = is_aoe, min_dmg, max_dmg
        self.accuracy, self.stun_chance, self.position_shift = (
            accuracy,
            stun_chance,
            position_shift,
        )
        self.target_type, self.effect, self.description = (
            target_type,
            effect or {},
            description,
        )


class Entity:
    def __init__(
        self,
        id_str: str,
        name: str,
        max_hp: int,
        spd: int,
        team: str,
        is_boss: bool = False,
        size: int = 1,
    ):
        self.id, self.name, self.team, self.is_boss, self.size = (
            id_str,
            name,
            team,
            is_boss,
            size,
        )
        self.max_hp, self.hp, self.spd = max_hp, max_hp, spd
        self.position = 1
        self.occupied_positions: List[int] = []
        self.is_stunned = False
        self.buffs, self.debuffs, self.status_effects = [], [], []
        self.soul_bound_target = None
        self.skills: List[Skill] = []
        self.current_initiative = 0
        self.initiative_tiebreaker = 0
        self.bonus_atk, self.bonus_def, self.bonus_acc = 0, 0, 0.0

    def is_alive(self) -> bool:
        return self.hp > 0

    def has_taunt(self) -> bool:
        return any(b.get("type") == "taunt" for b in self.buffs)

    def get_effective_spd(self) -> int:
        val = self.spd + sum(
            b.get("value", 0) for b in self.buffs if b.get("type") == "spd_up"
        )
        val -= sum(
            d.get("value", 0) for d in self.debuffs if d.get("type") == "spd_down"
        )
        return max(1, val)

    def roll_initiative(self):
        self.current_initiative = random.randint(1, self.get_effective_spd())
        self.initiative_tiebreaker = random.randint(1, 1000)

    def take_damage(
        self,
        raw_dmg: int,
        team_entities: List["Entity"],
        logs: List[str],
        ignore_taunt: bool = False,
    ) -> int:
        if not self.is_alive():
            return 0
        if not ignore_taunt and not self.has_taunt():
            taunter = next(
                (
                    ally
                    for ally in team_entities
                    if ally.is_alive() and ally.has_taunt()
                ),
                None,
            )
            if taunter:
                logs.append(f"  🛡️ [도발] {taunter.name}이(가) 대신 공격을 받습니다!")
                return taunter.take_damage(
                    raw_dmg, team_entities, logs, ignore_taunt=True
                )

        reduced_raw = max(1, raw_dmg - self.bonus_def)
        def_mod = (
            1.0
            - sum(b.get("value", 0.0) for b in self.buffs if b.get("type") == "def_up")
            + sum(
                d.get("value", 0.0) for d in self.debuffs if d.get("type") == "def_down"
            )
        )

        final_dmg = int(reduced_raw * max(0.1, def_mod))
        self.hp = max(0, self.hp - final_dmg)

        if (
            self.soul_bound_target
            and self.soul_bound_target.is_alive()
            and (self.soul_bound_target in team_entities)
        ):
            transfer_dmg = int(final_dmg * 0.5)
            self.hp += transfer_dmg  # 전이된 만큼 돌려받음
            self.soul_bound_target.hp = max(0, self.soul_bound_target.hp - transfer_dmg)
            logs.append(
                f"  🔗 [영혼 결속] {self.soul_bound_target.name}이(가) 대신 {transfer_dmg} 피해 흡수!"
            )

        return final_dmg

    def heal(self, amount: int) -> int:
        if not self.is_alive():
            return 0
        actual = min(self.max_hp - self.hp, amount)
        self.hp += actual
        return actual

    def process_start_of_turn(self, logs: List[str]) -> bool:
        rem_status = []
        for s in self.status_effects:
            if s.get("type") == "bleed":
                self.hp = max(0, self.hp - s["damage"])
                logs.append(
                    f"  🩸 {self.name} 출혈 피해 {s['damage']}! (남은 HP: {self.hp})"
                )
                s["duration"] -= 1
                if s["duration"] > 0:
                    rem_status.append(s)
        self.status_effects = rem_status
        if self.is_stunned:
            self.is_stunned = False
            logs.append(f"  💫 {self.name} 기절! 턴을 소모합니다.")
            return False
        return self.is_alive()

    def tick_effects(self):
        self.buffs = [b for b in self.buffs if b["duration"] - 1 > 0]
        for b in self.buffs:
            b["duration"] -= 1
        self.debuffs = [d for d in self.debuffs if d["duration"] - 1 > 0]
        for d in self.debuffs:
            d["duration"] -= 1


# ==========================================
# 3. 전투 시스템
# ==========================================
class BattleManager:
    ACTION_DELAY_SECONDS = 1

    def __init__(self, run_manager, enemies: List[Entity]):
        self.rm = run_manager
        self.heroes = [h for h in run_manager.heroes if h.is_alive()]
        self.enemies = [e for e in enemies if e.is_alive()]
        self.rm.heroes = self.heroes
        self.turn_count = 1
        self.turn_order, self.next_actions, self.battle_logs = [], {}, []
        self._update_all_positions()

    def _update_all_positions(self):
        for team in [self.heroes, self.enemies]:
            cur_pos = 1
            for entity in team:
                entity.position = cur_pos
                entity.occupied_positions = list(range(cur_pos, cur_pos + entity.size))
                cur_pos += entity.size

    def _remove_defeated_units(self):
        self.heroes = [h for h in self.heroes if h.is_alive()]
        self.enemies = [e for e in self.enemies if e.is_alive()]
        self.rm.heroes = self.heroes
        self._update_all_positions()

    def plan_enemy_actions(self):
        self.next_actions.clear()
        for e in self.enemies:
            if not e.is_alive():
                continue
            skill = random.choice(e.skills)

            # 오크 기믹: HP 50% 이하 & 공증 없을 시 분노의 함성
            if (
                e.name == "오크"
                and e.hp <= e.max_hp * 0.5
                and not any(b.get("type") == "atk_up" for b in e.buffs)
            ):
                skill = next((s for s in e.skills if s.skill_id == "roar"), skill)
            # 늑대 기믹: 아군 늑대가 있고 하울링이 없을 때 높은 확률로 하울링
            elif (
                e.name == "늑대"
                and sum(1 for a in self.enemies if a.name == "늑대" and a.is_alive())
                > 1
                and random.random() < 0.4
            ):
                skill = next((s for s in e.skills if s.skill_id == "howl"), skill)
            # 부두술사 기믹: 영혼 결속
            elif (
                e.name == "부두술사"
                and not e.soul_bound_target
                and len([a for a in self.enemies if a.is_alive()]) > 1
            ):
                skill = next((s for s in e.skills if s.skill_id == "soul_bind"), skill)

            self.next_actions[e.id] = {
                "unit_name": e.name,
                "skill": skill,
                "is_aoe": skill.is_aoe,
            }

    def _format_status_text(self, entity: Entity) -> str:
        status_parts = []
        if entity.is_stunned:
            status_parts.append("💫 기절")

        for buff in entity.buffs:
            kind = buff.get("type")
            if kind == "taunt":
                status_parts.append("🛡️ 도발")
            elif kind == "atk_up":
                value = int(buff.get("value", 0) * 100)
                status_parts.append(f"⚔️ 공격+{value}%")
            elif kind == "def_up":
                value = int(buff.get("value", 0) * 100)
                status_parts.append(f"🛡️ 방어+{value}%")
            elif kind == "spd_up":
                status_parts.append(f"⚡ SPD+{buff.get('value', 0)}")

        for debuff in entity.debuffs:
            kind = debuff.get("type")
            if kind == "acc_down":
                value = int(debuff.get("value", 0) * 100)
                status_parts.append(f"🎯 명중-{value}%")
            elif kind == "spd_down":
                status_parts.append(f"🧭 SPD-{debuff.get('value', 0)}")
            elif kind == "def_down":
                value = int(debuff.get("value", 0) * 100)
                status_parts.append(f"🛡️ 방어-{value}%")

        for effect in entity.status_effects:
            if effect.get("type") == "bleed":
                status_parts.append(f"🩸 출혈({effect.get('damage', 0)})")

        return ", ".join(status_parts) if status_parts else "없음"

    def print_round_ui(self):
        title = f"[ ROUND {self.turn_count} ]"
        border = "═" * 62
        print(f"\n╔{border}╗")
        print(f"║ {title.center(60)} ║")
        print("║ 🛡️ [아군 파티]")
        for h in self.heroes:
            st = "💫" if h.is_stunned else ""
            status_text = self._format_status_text(h)
            print(
                f"║ {h.position:>4}열 | {h.name:<5} | HP: {h.hp:>3}/{h.max_hp:<3} | 주사위: {h.current_initiative:>2} | 상태: {status_text:<30} {st}"
            )

        print("╠" + "─" * 62 + "╣")
        print("║ 👾 [적군 파티]")
        for e in self.enemies:
            pos = (
                f"{e.occupied_positions[0]}열"
                if e.size == 1
                else f"{e.occupied_positions[0]}-{e.occupied_positions[-1]}열"
            )
            st = "💫" if e.is_stunned else ""
            status_text = self._format_status_text(e)
            print(
                f"║ {pos:>4} | {e.name:<6} | HP: {e.hp:>3}/{e.max_hp:<3} | 주사위: {e.current_initiative:>2} | 상태: {status_text:<30} {st}"
            )

        print("╠" + "─" * 62 + "╣")
        turn_ui = " ".join(
            [
                f"[{i+1} {u.name} {u.current_initiative}]"
                for i, u in enumerate(self.turn_order)
            ]
        )
        print(f"║ ⚡ 턴 순서: {turn_ui}")
        print("║ 🔮 적 행동 예고:")
        for act in self.next_actions.values():
            area = "광역" if act["is_aoe"] else f"{act['skill'].target_positions}열"
            print(f"║   • {act['unit_name']:<6} ➔ [{act['skill'].name}] ({area})")
        print("╚" + "═" * 62 + "╝")

    def _format_target_label(self, skill: Skill) -> str:
        if skill.target_type in ["self_buff", "all_allies_buff", "all_allies_heal"]:
            return "전체/자신"
        if skill.target_type == "ally_heal":
            return "아군1명"
        if not skill.target_positions:
            return "전체"

        positions = sorted(set(skill.target_positions))
        if len(positions) == 1:
            return f"{positions[0]}열"

        contiguous = all(
            positions[i] == positions[0] + i for i in range(len(positions))
        )
        if contiguous:
            return f"{positions[0]}-{positions[-1]}열"
        return f"{','.join(map(str, positions))}열"

    def _targets_in_range(self, candidates: List[Entity], skill: Skill) -> List[Entity]:
        return [
            entity
            for entity in candidates
            if entity.is_alive()
            and (
                not skill.target_positions
                or any(p in skill.target_positions for p in entity.occupied_positions)
            )
        ]

    def _shift_entity_position(
        self, team: List[Entity], target: Entity, shift: int
    ) -> None:
        if shift == 0 or target not in team or not target.is_alive():
            return
        if target.size > 1:
            self.battle_logs.append(
                f"    ↔ {target.name}은(는) 거대해서 위치가 흔들리지 않습니다!"
            )
            return

        current_index = team.index(target)
        new_index = max(0, min(len(team) - 1, current_index + shift))
        if new_index == current_index:
            return

        team.insert(new_index, team.pop(current_index))
        self._update_all_positions()

        direction_text = "뒤로 밀려났습니다" if shift > 0 else "앞으로 끌려왔습니다"
        self.battle_logs.append(
            f"    ↔ {target.name}이(가) {target.position}열로 {direction_text}!"
        )

    def execute_skill(
        self, user: Entity, skill: Skill, chosen_target: Optional[Entity] = None
    ):
        allies = self.heroes if user.team == "player" else self.enemies
        opponents = self.enemies if user.team == "player" else self.heroes
        atk_mult = 1.0 + sum(
            b.get("value", 0) for b in user.buffs if b.get("type") == "atk_up"
        )

        self.battle_logs.append(f"\n▶ [{user.name}]의 [{skill.name}]!")

        # 특수(버프/힐/결속) 처리
        if skill.target_type == "self_buff":
            user.buffs.append(skill.effect.copy())
            self.battle_logs.append(f"  ✨ {user.name} 강화! ({skill.description})")
            return
        if skill.target_type == "all_allies_buff":
            for a in allies:
                a.buffs.append(skill.effect.copy())
            self.battle_logs.append(f"  ⏳ 아군 전체 강화!")
            return
        if skill.target_type == "all_allies_heal":
            for a in allies:
                amount = random.randint(
                    skill.min_dmg, max(skill.min_dmg, skill.max_dmg)
                )
                self.battle_logs.append(f"  💖 {a.name} {a.heal(amount)} 회복!")
            return
        if skill.target_type == "ally_heal":
            target = chosen_target or user
            healed = target.heal(
                random.randint(skill.min_dmg, max(skill.min_dmg, skill.max_dmg))
            )
            self.battle_logs.append(
                f"  💖 {target.name}의 체력이 {healed} 회복되었습니다! (HP: {target.hp}/{target.max_hp})"
            )
            return
        if skill.skill_id == "soul_bind":
            other = [a for a in allies if a != user and a.is_alive()]
            if other:
                user.soul_bound_target = random.choice(other)
                self.battle_logs.append(
                    f"  💀 {user.name}이 {user.soul_bound_target.name}에게 피해를 50% 전이합니다!"
                )
            return

        targets = (
            self._targets_in_range(opponents, skill)
            if skill.is_aoe
            else ([chosen_target] if chosen_target else [])
        )

        for t in targets:
            acc_mod = sum(
                d.get("value", 0) for d in user.debuffs if d.get("type") == "acc_down"
            )
            final_acc = min(1.0, max(0.05, skill.accuracy + user.bonus_acc - acc_mod))

            if random.random() <= final_acc:
                base_dmg = random.randint(
                    skill.min_dmg, max(skill.min_dmg, skill.max_dmg)
                )
                total_dmg = int((base_dmg + user.bonus_atk) * atk_mult)

                dealt = t.take_damage(total_dmg, opponents, self.battle_logs)
                self.battle_logs.append(f"  💥 {t.name}에게 {dealt} 피해! (HP: {t.hp})")

                if skill.stun_chance > 0 and random.random() <= skill.stun_chance:
                    t.is_stunned = True
                    self.battle_logs.append(f"    💫 {t.name} 기절!")
                if skill.effect.get(
                    "type"
                ) == "bleed" and random.random() <= skill.effect.get("chance", 1.0):
                    t.status_effects.append(
                        {
                            "type": "bleed",
                            "damage": skill.effect["damage"],
                            "duration": skill.effect["duration"],
                        }
                    )
                    self.battle_logs.append(f"    🩸 {t.name} 출혈 부여!")
                if skill.effect.get("type") in ["def_down", "acc_down", "spd_down"]:
                    t.debuffs.append(skill.effect.copy())
                    self.battle_logs.append(f"    📉 {t.name} 디버프 부여!")
                if skill.effect.get("type") == "self_heal":
                    healed = user.heal(skill.effect["value"])
                    self.battle_logs.append(f"    ✨ {user.name} 체력 {healed} 회복!")
                if skill.position_shift != 0:
                    self._shift_entity_position(opponents, t, skill.position_shift)
            else:
                self.battle_logs.append(f"  ❌ {t.name} 회피 (빗나감)!")

    def _handle_potion_use(self, unit):
        potions = [item for item in self.rm.inventory if item.item_type == "potion"]
        if not potions:
            print("  ❌ 가방에 포션이 없습니다.")
            return False

        print("\n[ 가방 속 포션 ]")
        for i, p in enumerate(potions, 1):
            print(f"  [{i}] {p.name} (회복량: {p.effect_value})")
        print("  [0] 취소")

        p_sel = input("사용할 포션 번호: ").strip()
        if not p_sel.isdigit() or int(p_sel) == 0 or int(p_sel) > len(potions):
            return False

        selected_potion = potions[int(p_sel) - 1]

        print("\n누구에게 사용하시겠습니까?")
        for i, h in enumerate(self.heroes, 1):
            print(f"  [{i}] {h.name} (HP: {h.hp}/{h.max_hp})")

        h_sel = input("영웅 선택: ").strip()
        if not h_sel.isdigit() or int(h_sel) < 1 or int(h_sel) > len(self.heroes):
            return False

        target = self.heroes[int(h_sel) - 1]
        healed = target.heal(selected_potion.effect_value)
        self.rm.inventory.remove(selected_potion)

        self.battle_logs.append(
            f"  🧪 {unit.name}이(가) 가방에서 {selected_potion.name}을 꺼내 사용했습니다!"
        )
        self.battle_logs.append(
            f"  💖 {target.name}의 체력이 {healed} 회복되었습니다! (현재 HP: {target.hp})"
        )
        return True

    def start_battle(self) -> bool:
        while self.heroes and self.enemies:
            self.plan_enemy_actions()
            for u in self.heroes + self.enemies:
                u.roll_initiative()
            self.turn_order = sorted(
                self.heroes + self.enemies,
                key=lambda u: (u.current_initiative, u.initiative_tiebreaker),
                reverse=True,
            )
            self.print_round_ui()

            for unit in self.turn_order:
                if not unit.is_alive() or not self.heroes or not self.enemies:
                    continue
                self.battle_logs.clear()

                repeats = (
                    2 if (unit.name == "드래곤" and unit.hp <= unit.max_hp * 0.3) else 1
                )
                for rep in range(repeats):
                    can_act = (
                        unit.process_start_of_turn(self.battle_logs)
                        if rep == 0
                        else unit.is_alive()
                    )
                    if can_act:
                        if unit.team == "player":
                            for log in self.battle_logs:
                                print(log)
                            self.battle_logs.clear()

                            while True:
                                print(f"\n👉 [{unit.name}] 턴! 행동 번호 입력:")
                                for i, s in enumerate(unit.skills, 1):
                                    pos_text = self._format_target_label(s)
                                    hit_rate = int(round(s.accuracy * 100))
                                    print(
                                        f"  [{i}] {s.name:<10} | 타깃: {pos_text:<10} | 명중률: {hit_rate:>3}%    |   {s.description}"
                                    )

                                has_potion = any(
                                    item.item_type == "potion"
                                    for item in self.rm.inventory
                                )
                                if has_potion:
                                    print("  [P] 가방 (포션 사용)")

                                sel = input("선택: ").strip().upper()
                                if sel == "P" and has_potion:
                                    if self._handle_potion_use(unit):
                                        break  # 포션 사용 완료 시 턴 넘김
                                elif sel.isdigit() and 1 <= int(sel) <= len(
                                    unit.skills
                                ):
                                    skill = unit.skills[int(sel) - 1]
                                    target = None

                                    # 적 대상 & 단일 공격 스킬인 경우 타깃 선택 창 출력
                                    if (
                                        skill.target_type == "enemy"
                                        and not skill.is_aoe
                                    ):
                                        # 스킬의 타격 범위 내에 있는 적만 필터링
                                        valid_enemies = self._targets_in_range(
                                            self.enemies, skill
                                        )

                                        if not valid_enemies:
                                            print(
                                                "\n❌ 사거리 내에 타격 가능한 적이 없습니다. 다른 스킬을 선택하세요."
                                            )
                                            continue  # 스킬 선택 화면으로 되돌아감

                                        print(
                                            f"\n🎯 [{skill.name}] 공격 대상을 선택하세요:"
                                        )
                                        for idx, e in enumerate(valid_enemies, 1):
                                            pos_str = (
                                                f"{e.occupied_positions[0]}열"
                                                if e.size == 1
                                                else f"{e.occupied_positions[0]}-{e.occupied_positions[-1]}열"
                                            )
                                            print(
                                                f"  [{idx}] {pos_str} | {e.name} (HP: {e.hp}/{e.max_hp})"
                                            )
                                        print("  [0] 취소 (스킬 선택으로 돌아가기)")

                                        # 유효한 타깃 번호를 입력받을 때까지 반복
                                        is_canceled = False
                                        while True:
                                            t_sel = input("대상 번호 선택: ").strip()
                                            if t_sel == "0":
                                                is_canceled = True
                                                break
                                            if t_sel.isdigit() and 1 <= int(
                                                t_sel
                                            ) <= len(valid_enemies):
                                                target = valid_enemies[int(t_sel) - 1]
                                                break
                                            print("올바른 번호를 입력하세요.")

                                        if is_canceled:
                                            continue  # 취소 시 상위 반복문(스킬 선택)으로 돌아감
                                    elif skill.target_type == "ally_heal":
                                        valid_allies = [
                                            a for a in self.heroes if a.is_alive()
                                        ]
                                        print(
                                            f"\n🎯 [{skill.name}] 회복 대상을 선택하세요:"
                                        )
                                        for idx, a in enumerate(valid_allies, 1):
                                            print(
                                                f"  [{idx}] {a.name} (HP: {a.hp}/{a.max_hp})"
                                            )
                                        print("  [0] 취소 (스킬 선택으로 돌아가기)")

                                        is_canceled = False
                                        while True:
                                            t_sel = input("대상 번호 선택: ").strip()
                                            if t_sel == "0":
                                                is_canceled = True
                                                break
                                            if t_sel.isdigit() and 1 <= int(
                                                t_sel
                                            ) <= len(valid_allies):
                                                target = valid_allies[int(t_sel) - 1]
                                                break
                                            print("올바른 번호를 입력하세요.")

                                        if is_canceled:
                                            continue

                                    self.execute_skill(unit, skill, target)
                                    break  # 턴 종료
                        else:
                            act = self.next_actions.get(unit.id)
                            skill = act["skill"] if act else random.choice(unit.skills)
                            target = None
                            if skill.target_type == "enemy" and not skill.is_aoe:
                                valid_targets = self._targets_in_range(
                                    self.heroes, skill
                                )
                                target = (
                                    random.choice(valid_targets)
                                    if valid_targets
                                    else None
                                )
                            self.execute_skill(unit, skill, target)

                    self._remove_defeated_units()

                    for log in self.battle_logs:
                        print(log)
                    self.battle_logs.clear()
                    if not self.heroes or not self.enemies:
                        break
                    time.sleep(self.ACTION_DELAY_SECONDS)

            for u in self.heroes + self.enemies:
                u.tick_effects()
            self.turn_count += 1

        if self.heroes:
            gold = random.randint(150, 300)
            self.rm.gold += gold
            print(f"\n🏆 전투 승리! {gold} G 획득. (총 {self.rm.gold} G)")
            return True
        return False


# ==========================================
# 4. 전체 게임 런(Run) 매니저
# ==========================================
class RunManager:
    def __init__(self):
        self.gold = 500
        self.inventory = []
        self.enemy_serial = 0
        self.heroes = self._create_heroes()

    def _next_enemy_id(self, name: str) -> str:
        self.enemy_serial += 1
        return f"{name}_{self.enemy_serial}"

    def _create_heroes(self):
        warrior = Entity("warrior", "전사", 180, 8, "player")
        warrior.skills = [
            Skill(
                "bone_cleave",
                "뼈가르기",
                [1, 2],
                min_dmg=30,
                max_dmg=30,
                accuracy=0.8,
                position_shift=1,
                description="30 피해, 밀쳐내기",
            ),
            Skill(
                "whirlwind",
                "회전 격멸",
                [],
                is_aoe=True,
                min_dmg=20,
                max_dmg=20,
                accuracy=0.7,
                description="광역 20 피해",
            ),
            Skill(
                "taunt",
                "도발",
                [],
                target_type="self_buff",
                effect={"type": "taunt", "duration": 2},
                description="2턴 대신 맞기",
            ),
            Skill(
                "berserk",
                "광폭화",
                [],
                target_type="self_buff",
                effect={"type": "atk_up", "value": 0.2, "duration": 2},
                description="공격력 20% 증가",
            ),
        ]
        mage = Entity("mage", "마법사", 90, 15, "player")
        mage.skills = [
            Skill(
                "fireball",
                "파이어볼",
                [2, 3, 4],
                min_dmg=20,
                max_dmg=40,
                accuracy=0.8,
                description="20~40 피해",
            ),
            Skill(
                "chain_lightning",
                "체인라이트닝",
                [1, 2],
                min_dmg=5,
                max_dmg=15,
                stun_chance=0.65,
                description="65% 스턴",
            ),
            Skill(
                "time_warp",
                "시간왜곡",
                [],
                target_type="all_allies_buff",
                effect={"type": "spd_up", "value": 5, "duration": 2},
                description="파티 SPD +5",
            ),
            Skill(
                "armageddon",
                "아마겟돈",
                [],
                is_aoe=True,
                min_dmg=100,
                max_dmg=100,
                accuracy=0.1,
                description="광역 100 피해",
            ),
        ]
        priest = Entity("priest", "지원가", 120, 12, "player")
        priest.skills = [
            Skill(
                "holy",
                "신의 심판",
                [1, 2],
                min_dmg=15,
                max_dmg=25,
                description="15~25 피해",
            ),
            Skill(
                "heal",
                "치유",
                [],
                target_type="ally_heal",
                min_dmg=20,
                max_dmg=40,
                description="한 명의 아군을 20~40 회복",
            ),
            Skill(
                "sanctuary",
                "정화의 성역",
                [],
                target_type="all_allies_heal",
                min_dmg=15,
                max_dmg=20,
                description="파티 15~20 회복",
            ),
            Skill(
                "thorn",
                "가시덩굴",
                [1, 2, 3, 4],
                min_dmg=5,
                max_dmg=5,
                stun_chance=0.7,
                position_shift=-1,
                description="당기기, 70% 스턴",
            ),
        ]
        return [warrior, mage, priest]

    def _create_enemy(self, name: str) -> Entity:
        e = Entity(self._next_enemy_id(name), name, 1, 1, "enemy")
        if name == "고블린":
            e.max_hp, e.hp, e.spd = 35, 35, 14
            e.skills = [
                Skill("stab", "단검 찌르기", [1, 2], min_dmg=10, max_dmg=15),
                Skill(
                    "sand",
                    "모래 뿌리기",
                    [1, 2, 3, 4],
                    effect={"type": "acc_down", "value": 0.3, "duration": 2},
                ),
            ]
        elif name == "오크":
            e.max_hp, e.hp, e.spd = 80, 80, 7
            e.skills = [
                Skill(
                    "club",
                    "몽둥이 내리치기",
                    [1, 2],
                    min_dmg=25,
                    max_dmg=35,
                    stun_chance=0.2,
                ),
                Skill(
                    "roar",
                    "분노의 함성",
                    [],
                    target_type="self_buff",
                    effect={"type": "atk_up", "value": 0.25, "duration": 99},
                ),
            ]
        elif name == "늑대":
            e.max_hp, e.hp, e.spd = 45, 45, 16
            e.skills = [
                Skill(
                    "bite",
                    "물어뜯기",
                    [1, 2, 3, 4],
                    min_dmg=15,
                    max_dmg=20,
                    effect={"type": "bleed", "damage": 5, "duration": 2, "chance": 0.4},
                ),
                Skill(
                    "howl",
                    "하울링",
                    [],
                    target_type="all_allies_buff",
                    effect={"type": "atk_up", "value": 0.1, "duration": 2},
                ),
            ]
        elif name == "부두술사":
            e.max_hp, e.hp, e.spd = 50, 50, 11
            e.skills = [
                Skill(
                    "curse", "부패의 저주", [2, 3], is_aoe=True, min_dmg=15, max_dmg=35
                ),
                Skill("soul_bind", "영혼 결속", [], target_type="special"),
            ]
        return e

    def _event_node(self):
        print(f"\n{'═'*20} [ 이벤트: 신비한 제단 ] {'═'*20}")
        print("  [1] 🪶 신속의 깃털 : 선택 영웅 SPD +3")
        print("  [2] ❤️ 거인의 심장 : 파티 전원 체력 20 회복")

        while True:
            sel = input("선택 (1~2): ").strip()
            if sel == "2":
                for h in self.heroes:
                    h.heal(20)
                print("  ✨ 파티 전원의 체력이 20 회복되었습니다!")
                break
            elif sel == "1":
                hero_sel = input("영웅 선택 (1.전사 2.마법사 3.지원가): ").strip()
                if hero_sel.isdigit() and 1 <= int(hero_sel) <= len(self.heroes):
                    h_idx = int(hero_sel) - 1
                    self.heroes[h_idx].spd += 3
                    print(f"  ⚡ {self.heroes[h_idx].name}의 SPD 증가!")
                    break
                print("올바른 영웅 번호를 입력하세요.")
            else:
                print("올바른 이벤트 번호를 입력하세요.")

    def start_run(self):
        stages = [
            {
                "type": "combat",
                "name": "초입 전투",
                "enemies": ["고블린", "늑대", "오크"],
            },
            {"type": "event"},
            {
                "type": "combat",
                "name": "숲속 전투",
                "enemies": ["오크", "오크", "늑대"],
            },
            {"type": "choice"},
            {"type": "combat", "name": "중간 보스", "boss": "golem"},
            {
                "type": "combat",
                "name": "호위병 전투",
                "enemies": ["고블린", "고블린", "부두술사", "오크"],
            },
            {"type": "choice"},
            {"type": "combat", "name": "최종 보스", "boss": "dragon"},
        ]

        for idx, stage in enumerate(stages, 1):
            print(f"\n{'#'*40}\n STAGE {idx} \n{'#'*40}")
            for h in self.heroes:
                h.buffs, h.debuffs, h.is_stunned = [], [], False

            if stage["type"] == "event":
                self._event_node()
            elif stage["type"] == "choice":
                while True:
                    sel = input(
                        "\n갈림길입니다. [1] 모닥불 휴식(체력 30 회복)  [2] 상점 방문: "
                    ).strip()
                    if sel in ["1", "2"]:
                        break
                    print("올바른 선택지를 입력하세요.")

                if sel == "1":
                    for h in self.heroes:
                        h.heal(30)
                    print("\n🏕️ 휴식으로 파티 전원의 체력이 30 회복되었습니다.")
                else:
                    enter_shop_loop(self)
            elif stage["type"] == "combat":
                enemies = []
                if stage.get("boss") == "golem":
                    g = Entity("golem", "골렘", 350, 5, "enemy", is_boss=True, size=2)
                    g.skills = [
                        Skill(
                            "rock",
                            "암석 낙하",
                            [1, 2],
                            is_aoe=True,
                            min_dmg=20,
                            max_dmg=35,
                            accuracy=0.5,
                        ),
                        Skill(
                            "seismic",
                            "지진파",
                            [],
                            is_aoe=True,
                            min_dmg=5,
                            max_dmg=5,
                            accuracy=0.7,
                            effect={"type": "spd_down", "value": 8, "duration": 2},
                        ),
                        Skill(
                            "stone",
                            "바위 피부",
                            [],
                            target_type="self_buff",
                            effect={"type": "def_up", "value": 0.1, "duration": 2},
                        ),
                    ]
                    enemies = [g, self._create_enemy("오크")]
                elif stage.get("boss") == "dragon":
                    d = Entity(
                        "dragon", "드래곤", 800, 13, "enemy", is_boss=True, size=4
                    )
                    d.skills = [
                        Skill(
                            "breath",
                            "화염 브레스",
                            [],
                            is_aoe=True,
                            min_dmg=20,
                            max_dmg=40,
                            accuracy=0.6,
                        ),
                        Skill(
                            "claw",
                            "용의 발톱",
                            [1],
                            min_dmg=45,
                            max_dmg=45,
                            accuracy=0.7,
                        ),
                        Skill("roar", "용의 포효", [], is_aoe=True, stun_chance=0.4),
                    ]
                    enemies = [d]
                else:
                    enemies = [self._create_enemy(n) for n in stage["enemies"]]

                if not BattleManager(self, enemies).start_battle():
                    print("\n💀 파티 전멸... 런이 종료됩니다.")
                    return

        print("\n🎉 모든 스테이지 클리어! 최종 보스를 물리쳤습니다!")


if __name__ == "__main__":
    RunManager().start_run()
