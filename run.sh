#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE="$1"
if [[ -z "$IMAGE" ]]; then
    echo "Usage: $0 <image_path> [color=C] [size=N] [minarea=N] [epsilon=N] [mode=otsu|canny[,canny_hi=N][,canny_low=N]]"
    exit 1
fi
shift

COLOR="red"
SIZE="1200"
MODE="otsu"
MIN_AREA=""
EPSILON=""
CANNY_LOW=""
CANNY_HIGH=""

for arg in "$@"; do
    key="${arg%%=*}"
    val="${arg#*=}"
    case "$key" in
        color)   COLOR="$val" ;;
        size)    SIZE="$val" ;;
        minarea) MIN_AREA="$val" ;;
        epsilon) EPSILON="$val" ;;
        mode)
            IFS=',' read -ra parts <<< "$val"
            MODE="${parts[0]}"
            for part in "${parts[@]:1}"; do
                pkey="${part%%=*}"
                pval="${part#*=}"
                case "$pkey" in
                    canny_hi)  CANNY_HIGH="$pval" ;;
                    canny_low) CANNY_LOW="$pval" ;;
                esac
            done
            ;;
    esac
done

STEM="$(basename "${IMAGE%.*}")"
VECT="vect/${STEM}.txt"
OUT="preview/${STEM}.png"

source .venv/bin/activate

EXTRACT_ARGS=("$IMAGE" "--mode" "$MODE")
[[ -n "$MIN_AREA"   ]] && EXTRACT_ARGS+=("--minarea"    "$MIN_AREA")
[[ -n "$EPSILON"    ]] && EXTRACT_ARGS+=("--epsilon"    "$EPSILON")
[[ -n "$CANNY_LOW"  ]] && EXTRACT_ARGS+=("--canny-low"  "$CANNY_LOW")
[[ -n "$CANNY_HIGH" ]] && EXTRACT_ARGS+=("--canny-high" "$CANNY_HIGH")

python3 extract_contours.py "${EXTRACT_ARGS[@]}"
python3 preview_vectors.py "$VECT" --size "$SIZE" --color "$COLOR"

open "$OUT"
