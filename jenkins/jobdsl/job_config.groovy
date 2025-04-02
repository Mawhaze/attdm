// Docker build job for Assistant to the Dungeon Manager (ATDM)
pipelineJob('docker/build/attdm') {
  logRotator {
    numToKeep(10) //Only keep the last 10
  }
  definition {
    cpsScm {
      scm {
        git {
          remote {
            url('https://github.com/mawhaze/attdm.git')
            credentials('github_access_token')
          }
          branches('*/main')
          scriptPath('Jenkinsfile')
        }
      }
    }
  }
  triggers {
    scm('H/15 * * * *') // Poll SCM every 15 minutes.
  }
}