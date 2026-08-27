import threading
#동기 프로그래밍
import time
def find_users_sync(n):
    for i in range(1, n+1):
        print(f'{n}명중 {i}번 째 사용자 조회 중 ...')
        time.sleep(1)
    print(f'>총 {n}명 사용자 동기 조회 완료')   
def process_sync():
    start = time.time()
    find_users_sync(3)
    find_users_sync(2)
    find_users_sync(1)
    end = time.time()
    print(f'>>>동기 처리 총 소요 시간 : {end-start}')
process_sync() 

#비동기 프로그래밍   
import asyncio 
import time
async def find_users_async(n):
    for i in range(1, n+1):
        print(f'{n}명중 {i}번 째 사용자 조회 중 ...')
        await asyncio.sleep(2)
    print(f'>총 {n}명 사용자 비동기 조회 완료')   
async def process_async():
    start = time.time()
    await asyncio.gather(
        find_users_async(5),
        find_users_async(7),
        find_users_async(1),
    )
    end = time.time()
    print(f'>>>비동기 처리 총 소요 시간 : {end-start}')
asyncio.run( process_async()) 

# import asyncio
# import time

# async def find_users_async(n, start):
#     for i in range(1, n+1):
#         now = time.time() - start
#         print(f"[{now:5.2f}초] {n}명중 {i}번째 사용자 조회 중 ...")
#         await asyncio.sleep(2)   # 비동기 대기
#     now = time.time() - start
#     print(f"[{now:5.2f}초] >총 {n}명 사용자 비동기 조회 완료")
#     return f"{n}명 완료"

# async def process_async():
#     start = time.time()
#     results = await asyncio.gather(
#         find_users_async(3, start),
#         find_users_async(2, start),
#         find_users_async(1, start),
#     )
#     end = time.time()
#     print(">>> gather 결과:", results)
#     print(f">>> 비동기 처리 총 소요 시간 : {end-start:.2f}초")

# asyncio.run(process_async())