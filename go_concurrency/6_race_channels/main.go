package main

import (
	"log"

	"github.com/fsnotify/fsnotify"
)

type LogLevel int
type Dept int

const (
	_ = iota * 10
	DEBUG
	INFO
	ERROR
	WARNING
	CRITICAL
)

const (
	_ = iota
	BA
	DEV
	QA
	DA //Data Analytics
	DS // Data Science
)

type LogRecord struct {
	LogLevel LogLevel       `json:"level"`
	Dept     Dept           `json:"dept"`
	Msg      map[string]any `json:"msg"`
}

type Reuqest struct {
	LogLevel LogLevel
	Dept     Dept
	respChan chan chan LogRecord
}

func main() {
	// Create new watcher.
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		log.Fatal(err)
	}
	defer watcher.Close()

	// Start listening for events.
	go func() {
		for {
			select {
			case event, ok := <-watcher.Events:
				if !ok {
					return
				}
				log.Println("event:", event)
				if event.Has(fsnotify.Write) {
					log.Println("modified file:", event.Name)
				}
			case err, ok := <-watcher.Errors:
				if !ok {
					return
				}
				log.Println("error:", err)
			}
		}
	}()

	// Add a path.
	err = watcher.Add("/tmp")
	if err != nil {
		log.Fatal(err)
	}

	// Block main goroutine forever.
	<-make(chan struct{})
}
