class Item:
    """
    [아이템 데이터 모델 클래스]
    아이템 고유 레벨(1~5)에 맞춰 명칭, 수치(공격력/방어력/회복량 등), 가격을 동적으로 계산합니다.
    """
    def __init__(self, name: str, item_type: str, item_level: int, base_stat: int, base_price: int):
        self.item_level = item_level
        
        # 1. 아이템 자체 레벨(1~5)에 따른 스케일링 계수 산출
        level_multiplier = 1 + (item_level - 1) * 0.5  # 레벨당 효과 +50%
        price_multiplier = 1 + (item_level - 1) * 2.2  # 레벨당 가격 +220%

        # 2. 아이템 레벨별 수식어(품질 계급) 매핑
        quality_prefixes = {1: "하급", 2: "일반", 3: "고급", 4: "희귀", 5: "전설"}
        prefix = quality_prefixes.get(item_level, "일반")
        
        # 3. 엔티티 속성 설정
        self.name = f"[{prefix}] {name}"
        self.item_type = item_type
        self.effect_value = int(base_stat * level_multiplier)
        self.price = int(base_price * price_multiplier)
        # 무기류일 경우 레벨에 따른 명중률 보정값 적용
        self.accuracy = min(1.0, 0.85 + (item_level - 1) * 0.03) if item_type == 'weapon' else 1.0

    def __repr__(self):
        """출력 인터페이스용 문자열 라벨 변환"""
        stat_label = {
            'weapon': "공격력",
            'magic': "마법력",
            'armor': "방어력",
            'potion': "회복량",
            'antidote': "해독",
            'necklace': "공격력",
            'ring': "방어력",
            'attack_buff': "공격력 버프",
            'defense_buff': "방어력 버프"
        }.get(self.item_type, "효과")

        accuracy_text = f" | 명중률: {self.accuracy:.0%}" if self.item_type == 'weapon' else ""
        stat_text = "해독" if self.item_type == 'antidote' else f"{stat_label} +{self.effect_value}"
        return f"{self.name} | {stat_text}{accuracy_text} | 가격: {self.price} Gold"


class Shop:
    """
    [상점 로직 및 트랜잭션 관리 클래스]
    상점 종류에 맞는 카탈로그를 로드하고 구매/판매 트랜잭션을 처리합니다.
    """
    # 카테고리별 상점 품목 카탈로그 (이름, 분류, 아이템 레벨, 기본 스탯, 기본 가격) - 각 10개 구성
    SHOP_CATALOGS = {
        "무기 상점": [
            ("낡은 나무 몽둥이", "weapon", 1, 6, 45),
            ("무딘 철검", "weapon", 1, 8, 70),
            ("초보 용병의 검", "weapon", 2, 12, 110),
            ("튼튼한 강철검", "weapon", 2, 16, 150),
            ("숙련 전사의 대검", "weapon", 3, 23, 230),
            ("붉은 룬 블레이드", "weapon", 3, 28, 300),
            ("백전노장의 파괴검", "weapon", 4, 36, 420),
            ("용의 심장검", "weapon", 4, 43, 520),
            ("천명을 가르는 신검", "weapon", 5, 55, 700),
            ("세계수의 창세검", "weapon", 5, 70, 950)
        ],
        "방어구 상점": [
            ("헤진 천 조끼", "armor", 1, 3, 40),
            ("낡은 가죽 갑옷", "armor", 1, 5, 65),
            ("단단한 가죽 흉갑", "armor", 2, 8, 100),
            ("철판 덧댄 갑옷", "armor", 2, 11, 140),
            ("숙련 기사의 갑주", "armor", 3, 16, 220),
            ("은빛 수호 갑옷", "armor", 3, 20, 290),
            ("백전노장의 철벽갑", "armor", 4, 27, 400),
            ("용비늘 전신갑주", "armor", 4, 34, 520),
            ("불멸의 성기사 갑주", "armor", 5, 44, 700),
            ("천상을 두른 신성갑", "armor", 5, 58, 950)
        ],
        "포션 상점": [
            ("밍밍한 회복 물", "potion", 1, 15, 25),
            ("작은 응급 붕대", "potion", 1, 25, 40),
            ("따뜻한 회복 물약", "potion", 2, 40, 70),
            ("튼튼한 치유 물약", "potion", 2, 55, 100),
            ("고급 치유 영약", "potion", 3, 75, 150),
            ("생명력의 푸른 영약", "potion", 3, 95, 210),
            ("성스러운 치유 성배", "potion", 4, 125, 300),
            ("대현자의 회복 비약", "potion", 4, 165, 400),
            ("불멸의 생명수", "potion", 5, 220, 600),
            ("신의 은총을 담은 성수", "potion", 5, 300, 850)
        ],
        "떠돌이 잡상인": [
            ("빛바랜 구리 목걸이", "necklace", 1, 2, 50),
            ("금 간 행운의 반지", "ring", 1, 2, 50),
            ("조잡한 은 목걸이", "necklace", 2, 4, 90),
            ("싸구려 철제 반지", "ring", 2, 4, 90),
            ("푸른 마력 목걸이", "necklace", 3, 7, 160),
            ("숙련자의 수호 반지", "ring", 3, 7, 160),
            ("별빛을 머금은 목걸이", "necklace", 4, 11, 280),
            ("용의 비늘 반지", "ring", 4, 11, 280),
            ("천공의 지배자 목걸이", "necklace", 5, 18, 500),
            ("운명을 비트는 신왕의 반지", "ring", 5, 18, 500)
        ]
    }

    def __init__(self, shop_type: str):
        if shop_type not in self.SHOP_CATALOGS:
            raise ValueError("[오류] 존재하지 않는 상점 종류입니다.")
        self.shop_type = shop_type
        self.pending_failure_message = None
        self.inventory = self._generate_inventory()

    def _generate_inventory(self) -> list:
        """선택된 상점 카테고리의 10개 품목을 기반으로 Item 객체 리스트 생성"""
        inventory = []
        for name, item_type, item_level, base_stat, base_price in self.SHOP_CATALOGS[self.shop_type]:
            item = Item(name, item_type, item_level, base_stat, base_price)
            inventory.append(item)
        return inventory

    def display_goods(self):
        """판매 상품 목록 출력 (10개 품목 전체)"""
        print(f"\n================ [ {self.shop_type} ] ================")
        print(f"어서오세요! {self.shop_type}입니다.")
        print("--------------------------------------------------")
        for idx, item in enumerate(self.inventory, 1):
            print(f"[{idx:2d}] {item}")
        print("================================------------------")

    def display_player_inventory(self, player):
        """플레이어 소지 아이템 및 판매 환급액(50%) 출력"""
        print("\n================ [ 판매할 아이템 ] ================")
        if not player['inventory']:
            print("판매할 아이템이 없습니다.")
        else:
            for idx, item_name in enumerate(player['inventory'], 1):
                item = self._find_inventory_item(item_name)
                sell_price = item.price // 2 if item else 0
                print(f"[{idx}] {item_name} | 판매 가격: {sell_price} Gold")
        print("================================================")

    def _find_inventory_item(self, item_name: str):
        """플레이어 인벤토리 아이템 명칭 비교 서치 연산"""
        base_name = item_name.split("] ", 1)[-1]
        for catalog_list in self.SHOP_CATALOGS.values():
            for name, item_type, item_level, base_stat, base_price in catalog_list:
                temp_item = Item(name, item_type, item_level, base_stat, base_price)
                if temp_item.name.split("] ", 1)[-1] == base_name:
                    return temp_item
        return None

    def sell_item(self, player, inventory_index: int):
        """플레이어 아이템 판매 및 골드 지급"""
        if inventory_index < 0 or inventory_index >= len(player['inventory']):
            print("\n[오류] 존재하지 않는 인벤토리 번호입니다.")
            return False

        item_name = player['inventory'][inventory_index]
        item = self._find_inventory_item(item_name)
        sell_price = item.price // 2 if item else 10

        player['inventory'].pop(inventory_index)
        player['gold'] += sell_price
        print(f"\n[판매 완료] {item_name}을(를) 판매했습니다! (+{sell_price} Gold)")
        print(f"현재 골드: {player['gold']} G")
        return True

    def process_transaction(self, player, choice_index: int):
        """
        [트랜잭션 수행 Engine]
        예외 처리 통과 시 재화 차감, 인벤토리 append, 플레이어 스탯 실시간 가산 적용[cite: 4, 5]
        """
        # [예외 처리 1] 배열 범위 초과 (Out of Bounds) 방지[cite: 4, 5]
        if choice_index < 0 or choice_index >= len(self.inventory):
            print("\n[오류] 존재하지 않는 상품 번호입니다. 다시 선택해주세요.")
            return False

        target_item = self.inventory[choice_index]

        # [예외 처리 2] 잔액 무결성 검증: Player_Gold >= Item_Price[cite: 4, 5]
        if player['gold'] < target_item.price:
            self.pending_failure_message = (
                "\n#################################"
                f"\n[구매 실패] 골드가 부족합니다! (소지: {player['gold']} G / 필요: {target_item.price} G)"
            )
            return False

        # [데이터 동기화]
        player['gold'] -= target_item.price  
        player['inventory'].append(target_item.name)[cite: 4, 5]  

        # 스탯 가산 연산
        if target_item.item_type == 'weapon':
            player['attack'] += target_item.effect_value
            player['accuracy'] = target_item.accuracy
            print(f"\n[구매 완료] {target_item.name}을(를) 장착했습니다! (공격력 +{target_item.effect_value}, 명중률 {target_item.accuracy:.0%})")
        elif target_item.item_type == 'armor':
            player['defense'] += target_item.effect_value
            print(f"\n[구매 완료] {target_item.name}을(를) 장착했습니다! (방어력 +{target_item.effect_value})")
        elif target_item.item_type == 'potion':
            player['hp'] += target_item.effect_value
            print(f"\n[구매 완료] {target_item.name}을(를) 사용했습니다! (HP +{target_item.effect_value})")
        elif target_item.item_type == 'necklace':
            player['attack'] += target_item.effect_value
            print(f"\n[구매 완료] {target_item.name}을(를) 장착했습니다! (공격력 +{target_item.effect_value})")
        elif target_item.item_type == 'ring':
            player['defense'] += target_item.effect_value
            print(f"\n[구매 완료] {target_item.name}을(를) 장착했습니다! (방어력 +{target_item.effect_value})")

        print(f"남은 골드: {player['gold']} G")
        return True


# ==========================================
# 실행 메인 루프 (상점 종류 선택 및 예외 처리)[cite: 4, 5]
# ==========================================
def enter_shop_loop(player, shop_type: str):
    """지정된 상점 종류로 진입하여 구매/판매 루프 실행"""
    shop = Shop(shop_type)
    merchant_message = "상점 주인: 마음에 드는 물건을 골라보시게!"

    while True:
        shop.display_goods()
        print(f"현재 보유 골드: {player['gold']} G | 공격력: {player['attack']} | 방어력: {player['defense']} | HP: {player['hp']}")
        if shop.pending_failure_message:
            print(shop.pending_failure_message)
            shop.pending_failure_message = None
        
        print(f"\n{merchant_message}")
        user_input = input("\n구매: 아이템 번호(1~10) / 판매: s / 나가기: 0: ").strip().lower()

        # [예외 처리 3] 판매(s) 모드 전환 및 비정수 예외 처리[cite: 4, 5]
        if user_input == 's':
            shop.display_player_inventory(player)
            sell_input = input("판매할 아이템 번호를 입력하세요 (취소: 0): ").strip()
            if not sell_input.isdigit():
                print("\n[오류] 숫자로만 입력해주세요.")
                continue
            sell_choice = int(sell_input)
            if sell_choice == 0:
                continue
            shop.sell_item(player, sell_choice - 1)
            merchant_message = "상점 주인: 또 판매할 물건이 있으면 가져오시게!"
            continue

        if not user_input.isdigit():
            print("\n[오류] 숫자로만 입력해주세요.")
            continue

        choice = int(user_input)

        if choice == 0:
            print(f"\n[{shop_type}]에서 나갑니다.")
            break

        purchase_succeeded = shop.process_transaction(player, choice - 1)
        if purchase_succeeded is False:
            merchant_message = "상점 주인: 돈이 부족하니 다음에 오시게!"
        else:
            merchant_message = "상점 주인: 마음에 드는 물건을 골라보시게!"


# 시스템 실행 시뮬레이션
if __name__ == "__main__":
    player_data = {
        'hp': 100,
        'attack': 10,
        'defense': 5,
        'gold': 1000,
        'inventory': [],
        'buffs': [],
        'debuffs': [],
        'status_effects': []
    }

    # 상점 카테고리 선택 메뉴
    shop_menu_map = {
        "1": "무기 상점",
        "2": "방어구 상점",
        "3": "포션 상점",
        "4": "떠돌이 잡상인"
    }

    while True:
        print("\n========== 마을 상가 구역 ==========")
        print("1. 무기 상점")
        print("2. 방어구 상점")
        print("3. 포션 상점")
        print("4. 떠돌이 잡상인 (장신구)")
        print("0. 마을로 돌아가기")

        shop_choice = input("입장할 상점을 선택하세요: ").strip()

        if shop_choice == '0':
            print("\n상가 구역을 떠납니다.")
            break

        if shop_choice not in shop_menu_map:
            print("\n!! 올바른 상점 번호를 선택해주세요 (1~4) !!")
            continue

        selected_shop = shop_menu_map[shop_choice]
        enter_shop_loop(player_data, shop_type=selected_shop)