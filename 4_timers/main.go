package main

import (
	"fmt"
	"time"
)

func costlyFunction(channel chan<- bool) {
	time.Sleep(5 * time.Second)
	channel <- true

}

func CostlyFuncAnalysis() {
	timer := time.NewTimer(2 * time.Millisecond)
	channel := make(chan bool)
	go costlyFunction(channel)

	select {
	case t := <-timer.C:
		fmt.Println("2 Seconds timed out")
		fmt.Printf("Timer: %#v", t)
	case f := <-channel:
		fmt.Println("Costly Functions")
		fmt.Printf("Costly operation completed.%v\n", f)

	}

}

func TimersAndTickers() {
	timerChan := time.NewTimer(1 * time.Second)
	tickerChan := time.NewTicker(1 * time.Millisecond)
	count := 0

	for {

		select {
		case timedOut := <-timerChan.C:
			fmt.Printf("Timed out at : %s\n", timedOut.Format("02-01-2006 03:04:05 PM"))
			fmt.Printf("Each second has: %d microseconds\n", count)
			return
		case ticker := <-tickerChan.C:
			fmt.Printf("Ticking at: \033[38;5;10m%s\033[0m\n", ticker.Format("02-01-2006 03:04:05 PM"))
			count += 1

		}

	}

}

func MonitorCPUusageWithSelect(monitorTime int) {
	ticker := time.NewTicker(time.Duration(monitorTime) * time.Millisecond)
	prevCpuUsage := 0
	threshold := 50
	alert := false
	for !alert {

		select {
		case checkedAt := <-ticker.C:
			CurrentCpuUsage := getCPUusage()
			if prevCpuUsage >= threshold && CurrentCpuUsage >= threshold {
				ticker.Stop()
				alert = true
				fmt.Printf("\033[38;5;9m[%s]: Cpu Usage has been more than threshold(%d), currentUsage: %d\033[0m\n",
					checkedAt.Format("02-01-2006 03:04:05 PM"), threshold, CurrentCpuUsage)
			} else {
				fmt.Printf("\033[38;5;10m[%s]: Cpu Usage chedked it is below threshold(%d), currentUsage: %d\033[0m\n",
					checkedAt.Format("02-01-2006 03:04:05 PM"), threshold, CurrentCpuUsage)
			}
			prevCpuUsage = CurrentCpuUsage

		}

	}
}

func MonitorCPUusageWithoutSelect(monitorTime int) {
	var highTime time.Time
	ticker := time.NewTicker(time.Duration(monitorTime) * time.Millisecond)
	prevCpuUsage := 0
	threshold := 85
	alertNow := false

	for !alertNow {
		highTime = <-ticker.C
		currentCPUUsage := getCPUusage()
		if prevCpuUsage >= threshold && currentCPUUsage >= threshold {
			ticker.Stop()
			alertNow = true

		} else {
			fmt.Printf("\033[38;5;10m[%s] Cpu Usage: %d%% within threshold (%d%%)\033[0m\n",
				highTime.Format("02-01-2006 03:04:05.000 PM"), currentCPUUsage, threshold)
		}

		prevCpuUsage = currentCPUUsage
	}

	fmt.Printf("\033[38;5;9m[%s] [ALERT] Cpu Usage: %d%% NOT WITHIN THRESHOLD threshold (%d%%)\033[0m\n",
		highTime.Format("02-01-2006 03:04:05 PM"), prevCpuUsage, threshold)

}

func MonitorCPUusageWithTimer(monitorTime int) {

	timeChan := time.NewTimer(time.Duration(monitorTime) * time.Second)
	prevCpuUsage := 0
	const threshold = 80

	for timeNow := range timeChan.C {

		currentCpuUsage := getCPUusage()
		if prevCpuUsage >= threshold && currentCpuUsage >= threshold {
			timeChan.Stop()
			fmt.Printf("\033[38;5;9m[%s]Cpu Usage: %d%%, Threshold: %d%%\033[0m\n",
				timeNow.Format("02-01-2006 03:04:05.000 PM"), currentCpuUsage, threshold)
			return

		} else {
			fmt.Printf("\033[38;5;10m[%s]Cpu Usage: %d%%, Threshold: %d%%\033[0m\n",
				timeNow.Format("02-01-2006 03:04:05.000 PM"), currentCpuUsage, threshold)
			prevCpuUsage = currentCpuUsage
			timeChan.Reset(time.Duration(monitorTime) * time.Second)

		}

	}

}

func main() {

	MonitorCPUusageWithTimer(1)
}
