package main

import (
	"fmt"
	"math/rand"
	"os"
	"time"

	"github.com/go-toast/toast"
)

func MonitorCPU(monitorTime int) (message string) {
	file, _ := os.Create("cpu_logs.log")
	defer file.Close()

	timer := time.NewTicker(time.Duration(monitorTime) * time.Second)
	defer timer.Stop()

	prevUsage := 0
	const THRESHOLD = 85

	for timeNow := range timer.C {
		currentUsage := rand.Intn(100) // this is only simulation
		if prevUsage >= THRESHOLD && currentUsage >= THRESHOLD {
			timer.Stop()

			return fmt.Sprintf("[%s] Concerning Cpu Usage!\nCurrent Reading: %d%%, Previous Reading %d%%",
				timeNow.Format("02-01-2006 03:04:05.000 PM"), currentUsage, prevUsage)
		} else {
			fmt.Fprintf(file, "[%s] Cpu Usage: %d%%, Threshold set: %d%%\n",
				timeNow.Format("02-01-2006 03:04:05.000 PM"), currentUsage, THRESHOLD)

			prevUsage = currentUsage

		}
	}
	return
}

func main() {
	message := MonitorCPU(1)
	notification := toast.Notification{
		AppID:   "CPU Notification",
		Title:   "Spike in CPU Usage",
		Message: message,
	}

	notification.Push()

}
