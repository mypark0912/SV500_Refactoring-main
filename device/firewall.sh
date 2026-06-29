#!/bin/sh
# /opt/firewall.sh
# 특정 공인 IP + 대역만 허용, 나머지 전부 차단
#
# ALLOWED_IP / ALLOWED_SUBNET 은 webserver 가 FRP 설정(FRP.host / FRP.allowIP)을
# 반영해 생성하는 /opt/firewall.env 로 덮어쓴다. env 파일이 없으면 아래 기본값 사용.
# (webserver 측 생성 로직: routes/setting.py 의 save_firewall_* / _apply_firewall)

LOCAL_NETS="192.168.0.0/16 172.16.0.0/12 10.0.0.0/8"

# 허용할 공인 IP (FRP 서버) — 기본값(Public FRP 서버)
ALLOWED_IP="13.125.5.143"

# 허용할 공인 IP 대역 — 기본값
ALLOWED_SUBNET="222.99.175.0/24"

# 허용 포트
ALLOWED_PORTS="22 443"

LOCAL_ONLY_PORTS="22 4000 502 8086 5000 5001"

# webserver 가 생성한 동적 설정으로 덮어쓰기 (있으면)
[ -f /opt/firewall.env ] && . /opt/firewall.env

# 초기화
iptables -F
iptables -X

# 기본 정책
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# loopback
iptables -A INPUT -i lo -j ACCEPT

# 수립된 연결 응답 허용 (frpc 터널 유지)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# === 내부 네트워크 허용 ===
for net in $LOCAL_NETS; do
  for port in $LOCAL_ONLY_PORTS; do
    iptables -A INPUT -s $net -p tcp --dport $port -j ACCEPT
  done
  iptables -A INPUT -s $net -p icmp -j ACCEPT
done

# === 특정 공인 IP 허용 (FRP 서버 등) — 공백 구분 다중 허용 / 비어있으면 규칙 없음 ===
for ip in $ALLOWED_IP; do
  for port in $ALLOWED_PORTS; do
    iptables -A INPUT -s $ip -p tcp --dport $port -j ACCEPT
  done
done

# === 특정 공인 대역 허용 (관리자 허용 IP 대역) — 공백 구분 다중 허용 / 비어있으면 규칙 없음 ===
for subnet in $ALLOWED_SUBNET; do
  for port in $ALLOWED_PORTS; do
    iptables -A INPUT -s $subnet -p tcp --dport $port -j ACCEPT
  done
done

# === 나머지 전부 차단 ===
iptables -A INPUT -j DROP

echo "===== Firewall Applied ====="
echo "Allowed IP:     $ALLOWED_IP"
echo "Allowed Subnet: $ALLOWED_SUBNET"
echo "Local Network:  $LOCAL_NETS"
echo "Allowed Ports:  $ALLOWED_PORTS"
echo "============================"
iptables -L -n --line-numbers
