#include "Animate.h"
#include "config.h"

#if Animate_Choice != 0
int Animate_key = -1; //初始化图标显示帧数
#endif

#if Animate_Choice == 1
#include "img/astronaut.h"
#elif Animate_Choice == 2
#include "img/hutao.h"
#elif Animate_Choice == 3 // cubes1
#include "img/cubes1.h"
#elif Animate_Choice == 4 // cube2
#include "img/cube2.h"
#elif Animate_Choice == 5 // bitcoin
#include "img/bitcoin.h"
#elif Animate_Choice == 6 // ethereum
#include "img/ethereum.h"
#elif Animate_Choice == 7 // loading
#include "img/loading.h"
#endif

void imgAnim(const uint8_t **Animate_value, uint32_t *Animate_size)
{
#if Animate_Choice != 0
    Animate_key++;
#endif

//太空人起飞
#if Animate_Choice == 1
    *Animate_value = astronaut[Animate_key];
    *Animate_size = astronaut[Animate_key];
    if (Animate_key >= 9)
        Animate_key = -1;
//胡桃摇
#elif Animate_Choice == 2
    *Animate_value = hutao[Animate_key];
    *Animate_size = hutao_size[Animate_key];
    if (Animate_key >= 31)
        Animate_key = -1;
#elif Animate_Choice == 3 // cubes1
    *Animate_value = cubes1[Animate_key];
    *Animate_size = cubes1_size[Animate_key];
    // 假设 cubes1 动画有 80 帧 (索引 0-79)。请根据实际帧数修改此处的 79 (应为 总帧数 - 1)。
    if (Animate_key >= 79) 
        Animate_key = -1;
#elif Animate_Choice == 4 // cube2
    *Animate_value = cube2[Animate_key];
    *Animate_size = cube2_size[Animate_key];
    if (Animate_key >= 99)
        Animate_key = -1;
#elif Animate_Choice == 5 // bitcoin
    *Animate_value = bitcoin[Animate_key];
    *Animate_size = bitcoin_size[Animate_key];
    if (Animate_key >= 52)
        Animate_key = -1;
#elif Animate_Choice == 6 // ethereum
    *Animate_value = ethereum[Animate_key];
    *Animate_size = ethereum_size[Animate_key];
    if (Animate_key >= 119)
        Animate_key = -1;
#elif Animate_Choice == 7 // loading
    *Animate_value = loading[Animate_key];
    *Animate_size = loading_size[Animate_key];
    if (Animate_key >= 59)
        Animate_key = -1;
#endif
}