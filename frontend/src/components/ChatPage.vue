<template>
  <div class="chat-page" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <AgentSidebar :collapsed="isSidebarCollapsed" @toggle="isSidebarCollapsed = !isSidebarCollapsed" />

    <div class="chat-content">
      <TopHeader />

      <main class="chat-main">
        <MinutesWorkflowPanel
          :workflow-status="workflowStatus"
          :status-created="STATUS.CREATED"
          :status-drafting="STATUS.DRAFTING"
          :source-text="sourceText"
          :audio-file-name="audioFileName"
          :can-generate="canGenerate"
          :is-sending="isSending"
          :displayed-minutes="displayedMinutes"
          :minute-candidates="minuteCandidates"
          @update:source-text="sourceText = $event"
          @audio-change="handleAudioChange"
          @generate="generateMinutes"
          @adopt="adoptCandidate"
          @edit="editCandidate"
        />

        <ProgressPanel
          v-if="progressLogs.length || currentPhase || streamError || isSending"
          :progress-logs="progressLogs"
          :current-phase="currentPhase"
          :stream-error="streamError"
          :is-sending="isSending"
        />
      </main>

      <MinutesReviewFooter
        v-if="workflowStatus === STATUS.WAITING_FOR_REVIEW"
        ref="reviewFooterRef"
        :input-text="inputText"
        :placeholder-text="placeholderText"
        :can-send="canSend"
        :is-sending="isSending"
        @update:input-text="inputText = $event"
        @resize="resizeTextarea"
        @send="sendMessage"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import AgentSidebar from "./AgentSidebar.vue";
import MinutesReviewFooter from "./MinutesReviewFooter.vue";
import MinutesWorkflowPanel from "./MinutesWorkflowPanel.vue";
import ProgressPanel from "./ProgressPanel.vue";
import TopHeader from "./TopHeader.vue";
import { createJob, getJob, JOB_STATUS, normalizeJobForUi, reviewJob } from "../services/minutesClient";

const reviewFooterRef = ref(null);
const inputText = ref("");
const sourceText = ref("");
const audioFileName = ref("");
const isSending = ref(false);
const progressLogs = ref([]);
const currentPhase = ref("");
const streamError = ref("");
const currentJobId = ref(null);
const selectedCandidateIndex = ref(0);
const isSidebarCollapsed = ref(false);
const STATUS = JOB_STATUS;
const workflowStatus = ref(STATUS.CREATED);
const adoptedMinutes = ref("");
const minuteCandidates = ref([]);
const placeholderText = "指示してください";

const canSend = computed(() => inputText.value.trim().length > 0);
const canGenerate = computed(() => sourceText.value.trim().length > 0 || Boolean(audioFileName.value));
const displayedMinutes = computed(() => adoptedMinutes.value || minuteCandidates.value[0]?.text || "議事録はまだ生成されていません。");

const resetProgressState = () => {
  progressLogs.value = [];
  currentPhase.value = "";
  streamError.value = "";
};

const appendProgressLog = (phaseLabel, detail = "") => {
  progressLogs.value.push({ phaseLabel, detail });
};

const resizeTextarea = (textareaEl) => {
  const textarea = textareaEl ?? reviewFooterRef.value?.textareaRef?.value ?? reviewFooterRef.value?.textareaRef;
  if (!textarea) {
    return;
  }

  const maxHeight = 200;
  textarea.style.height = "auto";
  const nextHeight = Math.min(textarea.scrollHeight, maxHeight);
  textarea.style.height = `${nextHeight}px`;
  textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
};

const applyUiJob = (job) => {
  const uiJob = normalizeJobForUi(job);
  minuteCandidates.value = uiJob.candidates;
  selectedCandidateIndex.value = uiJob.selectedIndex;
  adoptedMinutes.value = uiJob.selectedCandidateText;

  switch (uiJob.status) {
    case STATUS.COMPLETED:
      workflowStatus.value = STATUS.COMPLETED;
      currentPhase.value = "議事録が確定しました。";
      appendProgressLog("完了", "議事録のレビューが完了しました。");
      return;
    case STATUS.WAITING_FOR_REVIEW:
      workflowStatus.value = STATUS.WAITING_FOR_REVIEW;
      currentPhase.value = "候補を確認し、採用または修正してください。";
      appendProgressLog("レビュー待ち", "候補を確認してください。");
      return;
    case STATUS.DRAFTING:
      workflowStatus.value = STATUS.DRAFTING;
      currentPhase.value = "議事録を作成中です...";
      return;
    case STATUS.CREATED:
    default:
      workflowStatus.value = STATUS.CREATED;
      currentPhase.value = "入力内容を準備してください。";
  }
};

const syncJobState = async (jobId) => {
  const latestJob = await getJob(jobId);
  applyUiJob(latestJob);
};

const handleAudioChange = (event) => {
  const file = event.target.files?.[0];
  audioFileName.value = file ? file.name : "";
};

const generateMinutes = () => {
  sendMessage();
};

const adoptCandidate = (candidate) => {
  selectedCandidateIndex.value = candidate.index ?? 0;
  adoptedMinutes.value = candidate.text;
  sendMessage("approve");
};

const editCandidate = (candidate) => {
  selectedCandidateIndex.value = candidate.index ?? 0;
  inputText.value = `以下の議事録を修正してください:\n${candidate.text}\n修正点: `;
  workflowStatus.value = STATUS.WAITING_FOR_REVIEW;
  nextTick(() => {
    resizeTextarea();
    (reviewFooterRef.value?.textareaRef?.value ?? reviewFooterRef.value?.textareaRef)?.focus();
  });
};

const sendMessage = async (promptText = "") => {
  if (isSending.value) {
    return;
  }

  const instruction = (promptText || inputText.value).trim();
  if (currentJobId.value && !instruction) {
    return;
  }
  if (!currentJobId.value && !canGenerate.value) {
    return;
  }

  resetProgressState();
  workflowStatus.value = STATUS.DRAFTING;
  isSending.value = true;

  try {
    if (!currentJobId.value) {
      appendProgressLog("ジョブ作成", "議事録作成ジョブを開始します。");
      currentPhase.value = "議事録ジョブを作成しています...";
      const payload = audioFileName.value
        ? { input_type: "audio", audio_path: audioFileName.value }
        : { input_type: "transcript", transcript: sourceText.value.trim() };
      const createdJob = await createJob(payload);
      currentJobId.value = createdJob.id;
      await syncJobState(createdJob.id);
      sourceText.value = "";
    } else {
      appendProgressLog("レビュー送信", "レビュー指示を送信しています。");
      currentPhase.value = "レビュー内容を反映しています...";
      await reviewJob(currentJobId.value, {
        selected_index: selectedCandidateIndex.value,
        instruction
      });
      await syncJobState(currentJobId.value);
      inputText.value = "";
    }
  } catch (error) {
    console.error("minutes request failed:", error);
    streamError.value = "議事録 API の呼び出しに失敗しました。時間をおいて再度お試しください。";
    currentPhase.value = "エラー";
    workflowStatus.value = currentJobId.value ? STATUS.WAITING_FOR_REVIEW : STATUS.CREATED;

  } finally {
    isSending.value = false;
    await nextTick();
    resizeTextarea();
  }
};

onMounted(() => {
  resizeTextarea();
});

watch(inputText, () => {
  nextTick(() => {
    resizeTextarea();
  });
});
</script>
