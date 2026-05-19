#!/bin/bash
INTERFACES="end1"
DEBOUNCE=30
LAST_RESTART=0
WAS_DOWN=1   # 부팅 직후 첫 UP 은 복구로 간주(초기 연결 보장)

ip monitor link | while read -r line; do
    for iface in $INTERFACES; do
        echo "$line" | grep -q "$iface" || continue

        # 다운 계열 이벤트: 다음 UP 을 '실제 복구'로 인식하기 위한 표시만
        if echo "$line" | grep -qE "NO-CARRIER|state DOWN|LOWERLAYERDOWN"; then
            WAS_DOWN=1
            continue
        fi

        # 여기부터는 UP 이벤트
        echo "$line" | grep -q "state UP" || continue

        # 실제 DOWN -> UP 복구가 아닌 단순 UP 재통지는 무시.
        # (링크가 안 끊겼는데 오는 UP 이벤트로 frpc/SSH 를 죽이지 않음)
        [ "$WAS_DOWN" = "1" ] || continue

        now=$(date +%s)
        # 디바운스: 짧은 시간 내 down/up 반복(flap)은 1회만 처리
        if [ $((now - LAST_RESTART)) -lt $DEBOUNCE ]; then
            WAS_DOWN=0
            continue
        fi
        LAST_RESTART=$now
        WAS_DOWN=0
        sleep 5
        # 링크가 실제로 끊겼다 복구된 경우에만 재시작 → web 빠르게 복구.
        # (이 시점엔 기존 frpc 연결/SSH 는 이미 끊겨 있으므로 추가 피해 없음)
        sudo systemctl restart frpc
        sudo systemctl restart mqClient
    done
done
